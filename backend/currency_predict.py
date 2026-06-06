#!/usr/bin/env python3
import sys
import os
import json
import time

try:
    import numpy as np
    import cv2
except Exception as e:
    print(json.dumps({"error": f"Missing dependency: {e}"}))
    sys.exit(2)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: currency_predict.py <frames_dir>"}))
        return 2

    frames_dir = sys.argv[1]
    if not os.path.exists(frames_dir):
        print(json.dumps({"error": f"Frames directory not found: {frames_dir}"}))
        return 3

    # Import TF lazily and set memory growth where possible
    try:
        import tensorflow as tf
        try:
            gpus = tf.config.list_physical_devices('GPU')
            for g in gpus:
                try:
                    tf.config.experimental.set_memory_growth(g, True)
                except Exception:
                    pass
        except Exception:
            pass
        from tensorflow.keras.applications import EfficientNetB0
        from tensorflow.keras.models import Sequential, load_model
        from tensorflow.keras.layers import Dropout, Dense, GlobalAveragePooling2D
        from tensorflow.keras.optimizers import Adam
    except Exception as ex:
        print(json.dumps({"error": f"TensorFlow import failed: {ex}"}))
        return 4

    height = 224
    width = 224
    channels = 3
    n_classes = 8
    input_shape = (height, width, channels)

    optimizer = Adam(learning_rate=0.0001)

    weights_path = os.path.join(os.path.dirname(__file__), 'model_5.h5')

    # Build model and try to load weights with multiple fallbacks
    try:
        efnb0 = EfficientNetB0(weights='imagenet', include_top=False, input_shape=input_shape)
        local_model = Sequential()
        local_model.add(efnb0)
        local_model.add(GlobalAveragePooling2D())
        local_model.add(Dropout(0.5))
        local_model.add(Dense(n_classes, activation='softmax'))
        local_model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['acc'])

        loaded_model = None
        # First try: load weights into constructed model
        try:
            local_model.load_weights(weights_path)
            loaded_model = local_model
        except Exception as e_load:
            print('Warning: could not load model weights via load_weights:', e_load, file=sys.stderr)

        # Second try: attempt to load full model file directly
        if loaded_model is None:
            try:
                loaded = load_model(weights_path, compile=False)
                loaded_model = loaded
            except Exception as e_load_model:
                print('load_model direct attempt failed:', e_load_model, file=sys.stderr)

        # Third try: try efficientnet.keras variant and load weights
        if loaded_model is None:
            try:
                import efficientnet.keras as efn
                efnb0_alt = efn.EfficientNetB0(weights='imagenet', include_top=False, input_shape=input_shape, classes=n_classes)
                model_alt = Sequential()
                model_alt.add(efnb0_alt)
                model_alt.add(GlobalAveragePooling2D())
                model_alt.add(Dropout(0.5))
                model_alt.add(Dense(n_classes, activation='softmax'))
                model_alt.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['acc'])
                model_alt.load_weights(weights_path)
                loaded_model = model_alt
            except Exception as e_effn:
                print('Could not load weights with efficientnet.keras:', e_effn, file=sys.stderr)

        # Final fallback: try load_model with FixedDropout custom object mapping
        if loaded_model is None:
            try:
                class FixedDropout(Dropout):
                    pass
                loaded = None
                try:
                    loaded = load_model(weights_path, compile=False, custom_objects={'FixedDropout': FixedDropout})
                    print('Loaded model using local FixedDropout mapping', file=sys.stderr)
                except Exception as e_load_local:
                    print('load_model with local FixedDropout failed:', e_load_local, file=sys.stderr)
                    try:
                        loaded = load_model(weights_path, compile=False)
                        print('Loaded model using plain load_model', file=sys.stderr)
                    except Exception as e_load_plain:
                        print('Plain load_model also failed:', e_load_plain, file=sys.stderr)
                        loaded = None

                if loaded is not None:
                    loaded_model = loaded
            except Exception as e_final:
                print('Final fallback load_model attempt failed:', e_final, file=sys.stderr)

        if loaded_model is None:
            raise RuntimeError('Failed to build/load model: all fallbacks exhausted')

        model = loaded_model
    except Exception as e:
        print(json.dumps({"error": f"Failed to build/load model: {e}"}))
        return 5

    # Read frames
    frame_files = sorted([os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
    imgs = []
    for p in frame_files:
        im = cv2.imread(p)
        if im is None:
            continue
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        im = cv2.resize(im, (width, height))
        imgs.append(im)

    if len(imgs) == 0:
        print(json.dumps({"error": "No frames found for prediction"}))
        return 6

    X = np.array(imgs, dtype=np.float32) / 255.0
    try:
        t0 = time.time()
        predict = model.predict(X, verbose=0)
        # print('Prediction finished in', time.time() - t0)
    except Exception as e:
        print(json.dumps({"error": f"Model predict failed: {e}"}))
        return 7

    label_map = {0: '10', 1: '100', 2: '20', 3: '200', 4: '2000', 5: '50', 6: '500', 7: 'Background'}
    predList = []
    for index in range(predict.shape[0]):
        pred = label_map.get(int(np.argmax(predict[index])), 'Background')
        predList.append(pred)
    from collections import Counter
    note = Counter(predList).most_common(1)[0][0]

    print(json.dumps({"prediction": note}))
    return 0


if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
