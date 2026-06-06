#!/usr/bin/env python3
"""
Extract text from external DOCX and PDF files and save into documentation/external_docs.
Usage: python backend/scripts/extract_external_docs.py
"""
import zipfile
import subprocess
import shutil
import os
import xml.etree.ElementTree as ET

PATHS = [
    "/Users/chirag/Desktop/vy/untitled p/mine/Finallllllll-me.docx",
    "/Users/chirag/Desktop/vy/untitled p/Empowering Independence_ A Solution for the Visually Impaired - CHIRAG.pdf",
]

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'documentation', 'external_docs')
OUT_DIR = os.path.normpath(OUT_DIR)
os.makedirs(OUT_DIR, exist_ok=True)


def extract_docx(path):
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read('word/document.xml')
            tree = ET.fromstring(xml)
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            texts = [t.text for t in tree.findall('.//w:t', ns) if t.text]
            return '\n'.join(texts)
    except Exception as e:
        return 'ERROR_DOCX:' + repr(e)


def extract_pdf(path):
    try:
        if shutil.which('pdftotext'):
            p = subprocess.run(['pdftotext', '-layout', path, '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
            if p.returncode == 0:
                return p.stdout
            else:
                return 'ERROR_PDF_pdftotext_rc:' + str(p.returncode) + ' stderr:' + p.stderr
        try:
            import PyPDF2
            with open(path, 'rb') as f:
                r = PyPDF2.PdfReader(f)
                pages = [(p.extract_text() or '') for p in r.pages]
                return '\n'.join(pages)
        except Exception as e2:
            return 'ERROR_PDF_PyPDF2:' + repr(e2)
    except Exception as e:
        return 'ERROR_PDF:' + repr(e)


def main():
    for p in PATHS:
        base = os.path.basename(p)
        out = os.path.join(OUT_DIR, base + '.txt')
        try:
            if os.path.exists(p):
                if p.lower().endswith('.docx'):
                    txt = extract_docx(p)
                elif p.lower().endswith('.pdf'):
                    txt = extract_pdf(p)
                else:
                    txt = 'UNSUPPORTED_FILE_TYPE'
                with open(out, 'w', encoding='utf-8') as f:
                    f.write(txt)
                print('WROTE:' + out)
            else:
                print('MISSING:' + p)
        except Exception as e:
            print('FAILED:' + p + ':' + repr(e))


if __name__ == '__main__':
    main()
