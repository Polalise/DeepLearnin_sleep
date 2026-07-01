from PIL import Image, ImageOps, ImageDraw
from pathlib import Path
src = Path(r'C:\workSpace\DeepLearnin_sleep\tmp_pdf_review')
pages = sorted(src.glob('page_*.png'))
pages = [p for p in pages if p.name != 'page_30.png']
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
sheet.save(src/'contact_sheet.png')
print(src/'contact_sheet.png')
