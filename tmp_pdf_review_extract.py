import fitz
from pathlib import Path
pdf = Path(r'C:\Users\human-23\Downloads\AI 기반 취침 전 수면 건강 예측 모델 개발.pdf')
out = Path(r'C:\workSpace\DeepLearnin_sleep\tmp_pdf_review')
out.mkdir(parents=True, exist_ok=True)
doc = fitz.open(pdf)
print('pages', doc.page_count)
all_text = []
for i, page in enumerate(doc, start=1):
    text = page.get_text('text')
    all_text.append(f'\n\n===== PAGE {i} =====\n{text}')
Path(out/'extracted_text.txt').write_text(''.join(all_text), encoding='utf-8')
for pno in range(doc.page_count):
    pix = doc[pno].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    pix.save(out / f'page_{pno+1:02d}.png')
print(out)
