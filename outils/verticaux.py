#!/usr/bin/env python3
"""Formats verticaux Niodoo (1080x1920) : stories « nouveau post » et vidéos Reels.

Usage :
    python3 outils/verticaux.py story posts/2026-10-18/1.jpg stories/2026-10-18.jpg
    python3 outils/verticaux.py reel reels/2026-10-18/reel.json

Un reel.json contient "images" : une liste d'images 1080x1920 déjà prêtes ou de
cartes à dessiner {"photo", "titre", "texte"} / {"titre", "texte", "fonce": true}.
La vidéo est enregistrée à côté du JSON (reel.mp4), avec une couverture (cover.jpg).
"""
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

ICI = os.path.dirname(os.path.abspath(__file__))
POL = os.path.join(ICI, "polices")
PHOTOS = os.path.join(ICI, "photos")
LOGO = os.path.join(ICI, "..", "marque", "avatar-niodoo.png")
W, H = 1080, 1920
OLIVE = (79, 90, 63)
GREIGE = (237, 234, 224)
SABLE = (226, 223, 210)
BLANC = (255, 255, 255)


def police(poids, taille):
    return ImageFont.truetype(os.path.join(POL, f"Manrope-{poids}.ttf"), taille)


def couper(d, texte, f, largeur):
    mots, lignes, cur = texte.split(), [], ""
    for m in mots:
        t = (cur + " " + m).strip()
        if d.textlength(t, font=f) <= largeur:
            cur = t
        else:
            lignes.append(cur)
            cur = m
    if cur:
        lignes.append(cur)
    return lignes


def entete(im, d, clair=True):
    logo = Image.open(LOGO).resize((96, 96))
    m = Image.new("L", (96, 96), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 95, 95), fill=255)
    im.paste(logo, (80, 110), m)
    d.text((196, 158), "NIODOO", font=police("ExtraBold", 40), fill=BLANC if clair else OLIVE, anchor="lm")


def photo_remplie(nom, w, h):
    p = Image.open(os.path.join(PHOTOS, nom + ".jpg")).convert("RGB")
    r = max(w / p.width, h / p.height)
    p = p.resize((int(p.width * r) + 1, int(p.height * r) + 1))
    x, y = (p.width - w) // 2, (p.height - h) // 2
    return p.crop((x, y, x + w, y + h))


def story(source, sortie):
    im = Image.new("RGB", (W, H), OLIVE)
    d = ImageDraw.Draw(im)
    entete(im, d)
    d.text((540, 330), "Nouveau post", font=police("ExtraBold", 64), fill=BLANC, anchor="mm")
    img = Image.open(source).convert("RGB").resize((864, 1080))
    im.paste(img, (108, 420))
    d.rounded_rectangle((260, 1600, 820, 1700), 50, fill=GREIGE)
    d.text((540, 1650), "À voir sur notre profil", font=police("Bold", 40), fill=OLIVE, anchor="mm")
    d.text((540, 1780), "niodoo.net", font=police("SemiBold", 38), fill=SABLE, anchor="mm")
    im.save(sortie, quality=90)


def carte(c, sortie):
    if c.get("photo"):
        im = Image.new("RGB", (W, H), OLIVE)
        im.paste(photo_remplie(c["photo"], W, 1150), (0, 0))
        d = ImageDraw.Draw(im)
        voile = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
        dv = ImageDraw.Draw(voile)
        for i in range(300):
            dv.line([(0, i), (W, i)], fill=(0, 0, 0, int(110 * (1 - i / 300))))
        im.paste(voile, (0, 0), voile)
        d = ImageDraw.Draw(im)
        entete(im, d)
        y = 1220
    else:
        fonce = c.get("fonce", True)
        im = Image.new("RGB", (W, H), OLIVE if fonce else GREIGE)
        d = ImageDraw.Draw(im)
        entete(im, d, clair=fonce)
        y = 700
    fonce_txt = bool(c.get("photo")) or c.get("fonce", True)
    ft, fx = police("ExtraBold", 84), police("Medium", 48)
    for ligne in couper(d, c["titre"], ft, 920):
        d.text((80, y), ligne, font=ft, fill=BLANC if fonce_txt else OLIVE)
        y += 102
    y += 30
    for ligne in couper(d, c.get("texte", ""), fx, 920):
        d.text((80, y), ligne, font=fx, fill=SABLE if fonce_txt else (34, 38, 29))
        y += 64
    if c.get("bouton"):
        y += 40
        d.rounded_rectangle((80, y, 600, y + 100), 50, fill=GREIGE if fonce_txt else OLIVE)
        d.text((340, y + 50), c["bouton"], font=police("Bold", 44), fill=OLIVE if fonce_txt else GREIGE, anchor="mm")
        y += 100
    if y > 1820:
        sys.exit(f"Texte trop long pour {sortie}")
    im.save(sortie, quality=92)


def reel(chemin):
    dossier = os.path.dirname(os.path.abspath(chemin))
    cfg = json.load(open(chemin))
    duree, fondu = cfg.get("duree", 2.6), 0.5
    tmp = tempfile.mkdtemp()
    fichiers = []
    for i, c in enumerate(cfg["images"]):
        f = os.path.join(tmp, f"{i}.jpg")
        if isinstance(c, str):
            Image.open(os.path.join(dossier, c) if not os.path.isabs(c) else c).convert("RGB").resize((W, H)).save(f, quality=92)
        else:
            carte(c, f)
        fichiers.append(f)
    Image.open(fichiers[0]).save(os.path.join(dossier, "cover.jpg"), quality=90)
    entrees, filtres = [], []
    for i, f in enumerate(fichiers):
        entrees += ["-loop", "1", "-t", str(duree + fondu), "-i", f]
        frames = int((duree + fondu) * 30)
        filtres.append(
            f"[{i}:v]scale=1188:2112,zoompan=z='min(zoom+0.0009,1.08)':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps=30,setsar=1,format=yuv420p[v{i}]")
    prec, decal = "v0", duree
    for i in range(1, len(fichiers)):
        filtres.append(f"[{prec}][v{i}]xfade=transition=fade:duration={fondu}:offset={decal:.2f}[x{i}]")
        prec, decal = f"x{i}", decal + duree
    total = duree * len(fichiers) + fondu
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *entrees,
           "-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
           "-filter_complex", ";".join(filtres), "-map", f"[{prec}]", "-map", f"{len(fichiers)}:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-shortest", "-movflags", "+faststart", os.path.join(dossier, "reel.mp4")]
    subprocess.run(cmd, check=True)
    print("Vidéo :", os.path.join(dossier, "reel.mp4"))


if __name__ == "__main__":
    if sys.argv[1] == "story":
        story(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "reel":
        reel(sys.argv[2])
