import fitz
from pathlib import Path
from PIL import Image, ImageDraw
pdf = Path(r'C:\Users\human-23\Downloads\AI 기반 취침 전 수면 건강 예측 모델 개발.pdf')
out = Path(r'C:\workSpace\DeepLearnin_sleep\tmp_pdf_review_v2')
out.mkdir(parents=True, exist_ok=True)
for old in out.glob('page_*.png'):
    old.unlink()
doc = fitz.open(pdf)
print('pages', doc.page_count)
texts=[]
for i,page in enumerate(doc, start=1):
    texts.append(f'\n\n===== PAGE {i} =====\n{page.get_text("text")}')
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    pix.save(out / f'page_{i:02d}.png')
(out/'extracted_text.txt').write_text(''.join(texts), encoding='utf-8')
# contact sheet
pages = sorted(out.glob('page_*.png'))
thumbs=[]
for p in pages:
    im=Image.open(p).convert('RGB')
    im.thumbnail((320,180))
    canvas=Image.new('RGB',(340,220),'white')
    x=(340-im.width)//2; y=28+(160-im.height)//2
    canvas.paste(im,(x,y))
    d=ImageDraw.Draw(canvas)
    d.text((10,8),p.stem.replace('page_','p.'),fill=(20,20,20))
    thumbs.append(canvas)
cols=5; rows=(len(thumbs)+cols-1)//cols
sheet=Image.new('RGB',(cols*340, rows*220),(245,246,248))
for idx,t in enumerate(thumbs):
    sheet.paste(t,((idx%cols)*340,(idx//cols)*220))
sheet.save(out/'contact_sheet.png')
print(out)
