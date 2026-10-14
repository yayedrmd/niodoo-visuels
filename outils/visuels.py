#!/usr/bin/env python3
"""Visuels Niodoo : génère des images 1080x1350 aux couleurs de Niodoo.

Usage :
    python3 outils/visuels.py posts/2026-10-16/post.json

Le fichier JSON contient une liste "images". Chaque image est enregistrée
dans le même dossier que le JSON (1.jpg, 2.jpg...). Le script affiche aussi
le chemin d'une planche d'aperçu pour vérifier le rendu avant publication.

Modèles : affiche, couverture, etape, liste, question
Thèmes  : clair (fond beige), fonce (fond vert olive)

Champs par modèle :
    affiche    : etiquette, titre, accroche, texte, slogan, centrer (true/false)
    couverture : etiquette, titre, accroche
    etape      : numero, titre, texte
    liste      : etiquette, titre, points (liste de phrases)
    question   : titre, texte, bouton

Pas d'emoji ni de flèche dans le texte des images : la police ne les
affiche pas, le script s'arrête avec un message si besoin.
"""
import json
import os
import re
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

try:
    from fontTools.ttLib import TTFont
except ImportError:  # la vérification des caractères est alors ignorée
    TTFont = None

ICI = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350
MARGE = 70
LARG = W - 2 * MARGE

OLIVE = (83, 93, 68)
BEIGE = (226, 223, 210)
BLANC = (255, 255, 255)
SOMBRE = (40, 45, 33)

THEMES = {
    "clair": {"fond": BEIGE, "titre": SOMBRE, "texte": OLIVE, "accent": OLIVE,
              "sur_accent": BLANC, "logo_fond": OLIVE, "logo_trait": BLANC},
    "fonce": {"fond": OLIVE, "titre": BLANC, "texte": BEIGE, "accent": BEIGE,
              "sur_accent": OLIVE, "logo_fond": BEIGE, "logo_trait": OLIVE},
}

DOSSIERS_POLICES = [os.path.join(ICI, "polices"), "/usr/share/fonts/truetype/google-fonts"]
PIED = "niodoo.net  ·  @niodoo_officiel"


def erreur(message):
    sys.exit("ERREUR : " + message)


def chemin_police(graisse):
    for dossier in DOSSIERS_POLICES:
        chemin = os.path.join(dossier, f"Poppins-{graisse}.ttf")
        if os.path.exists(chemin):
            return chemin
    erreur(f"police Poppins-{graisse}.ttf introuvable (cherchée dans {DOSSIERS_POLICES}).")


_polices = {}
_caracteres = {}


def police(graisse, taille):
    cle = (graisse, taille)
    if cle not in _polices:
        _polices[cle] = ImageFont.truetype(chemin_police(graisse), taille)
    return _polices[cle]


def preparer(texte, graisse):
    """Typographie française (espaces insécables) + refus des caractères absents."""
    texte = re.sub(r" ([?!:;»])", " \\1", texte)
    texte = texte.replace("« ", "« ").replace("'", "’")
    if TTFont:
        chemin = chemin_police(graisse)
        if chemin not in _caracteres:
            _caracteres[chemin] = set(TTFont(chemin).getBestCmap().keys())
        manquants = sorted({c for c in texte if c not in " \n" and ord(c) not in _caracteres[chemin]})
        if manquants:
            erreur(f"caractères non affichables {manquants} dans « {texte} ». "
                   "Retire les emojis et les flèches du texte des images.")
    return texte


def couper(d, texte, f, largeur):
    lignes = []
    for paragraphe in texte.split("\n"):
        ligne = ""
        for mot in [m for m in paragraphe.split(" ") if m]:
            essai = f"{ligne} {mot}".strip()
            if not ligne or d.textlength(essai, font=f) <= largeur:
                ligne = essai
            else:
                lignes.append(ligne)
                ligne = mot
        lignes.append(ligne)
    return lignes


def empiler(d, blocs, y0, y1, x=MARGE, largeur=LARG, centre=False, milieu=False):
    """Place des blocs de texte entre y0 et y1, en réduisant la taille si besoin.

    Chaque bloc : dict(texte, graisse, taille, interligne, couleur, ecart, puce).
    Retourne la position verticale sous le dernier bloc.
    """
    blocs = [dict(b, texte=preparer(b["texte"], b["graisse"])) for b in blocs if b.get("texte")]
    echelle = 1.0
    while echelle >= 0.55:
        mesures, total, ok = [], 0, True
        for b in blocs:
            f = police(b["graisse"], max(22, int(b["taille"] * echelle)))
            retrait = int(f.size * 1.1) if b.get("puce") else 0
            lignes = couper(d, b["texte"], f, largeur - retrait)
            if any(d.textlength(l, font=f) > largeur - retrait for l in lignes):
                ok = False
                break
            pas = int(f.size * b["interligne"])
            ecart = int(b.get("ecart", 0) * echelle)
            mesures.append((b, f, lignes, pas, ecart, retrait))
            total += len(lignes) * pas + ecart
        if ok and total <= y1 - y0:
            y = y0 + (y1 - y0 - total) // 2 if milieu else y0
            for b, f, lignes, pas, ecart, retrait in mesures:
                if b.get("puce"):
                    r = max(7, f.size // 5)
                    cy = y + int(f.size * 0.72)
                    d.ellipse([x, cy - r, x + 2 * r, cy + r], fill=b["couleur_puce"])
                for ligne in lignes:
                    tx = x + retrait
                    if centre:
                        tx = x + (largeur - d.textlength(ligne, font=f)) / 2
                    d.text((tx, y), ligne, font=f, fill=b["couleur"])
                    y += pas
                y += ecart
            return y
        echelle -= 0.05
    erreur("texte trop long pour l'image. Raccourcis le titre ou le texte.")


def logo(img, d, cx, cy, r, t):
    fichier = os.path.join(ICI, "logo.png")
    if os.path.exists(fichier):  # le vrai logo, s'il a été déposé
        image = Image.open(fichier).convert("RGBA").resize((2 * r, 2 * r), Image.LANCZOS)
        img.paste(image, (cx - r, cy - r), image)
        return
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=t["logo_fond"])
    s, epais, point = r * 0.42, max(3, int(r * 0.11)), r * 0.13
    a = (cx - s * 0.55, cy + s * 0.75)
    b = (cx - s * 0.55, cy - s * 0.55)
    c = (cx + s * 0.55, cy + s * 0.55)
    e = (cx + s * 0.55, cy - s * 0.75)
    d.line([a, b, c, e], fill=t["logo_trait"], width=epais, joint="curve")
    for p in (a, e):
        d.ellipse([p[0] - point, p[1] - point, p[0] + point, p[1] + point],
                  fill=t["logo_fond"], outline=t["logo_trait"], width=epais)


def cadre(img, d, t):
    logo(img, d, 110, 110, 40, t)
    d.text((168, 88), "NIODOO", font=police("Bold", 34), fill=t["accent"])
    d.text((MARGE, H - 100), PIED, font=police("Medium", 28), fill=t["texte"])


def pastille(d, x, y, texte, t, centre=False):
    texte = preparer(texte, "Medium")
    f = police("Medium", 30)
    largeur = d.textlength(texte, font=f) + 60
    if centre:
        x = (W - largeur) / 2
    d.rounded_rectangle([x, y, x + largeur, y + 60], 30, fill=t["accent"])
    d.text((x + 30, y + 30), texte, font=f, fill=t["sur_accent"], anchor="lm")
    return y + 60


def slogan(d, texte, t):
    d.line([MARGE, H - 170, W - MARGE, H - 170], fill=t["accent"], width=2)
    empiler(d, [dict(texte=texte, graisse="Bold", taille=44, interligne=1.2,
                     couleur=t["accent"])], H - 245, H - 180)


def bloc(texte, graisse, taille, interligne, couleur, ecart=0, **autres):
    return dict(texte=texte, graisse=graisse, taille=taille, interligne=interligne,
                couleur=couleur, ecart=ecart, **autres)


def m_affiche(img, d, t, s):
    haut = 260
    if s.get("etiquette"):
        haut = pastille(d, MARGE, 230, s["etiquette"], t) + 50
    bas = H - 270 if s.get("slogan") else H - 200
    empiler(d, [
        bloc(s.get("titre"), "Bold", 86, 1.12, t["titre"], 40),
        bloc(s.get("accroche"), "Medium", 52, 1.22, t["texte"], 40),
        bloc(s.get("texte"), "Regular", 39, 1.38, t["texte"]),
    ], haut, bas, milieu=bool(s.get("centrer")))
    if s.get("slogan"):
        slogan(d, s["slogan"], t)


def m_couverture(img, d, t, s):
    haut = 260
    if s.get("etiquette"):
        haut = pastille(d, MARGE, 230, s["etiquette"], t) + 50
    empiler(d, [
        bloc(s.get("titre"), "Bold", 96, 1.1, t["titre"], 44),
        bloc(s.get("accroche"), "Medium", 46, 1.25, t["texte"]),
    ], haut, H - 200, milieu=True)


def m_etape(img, d, t, s):
    d.ellipse([MARGE, 300, MARGE + 180, 480], fill=t["accent"])
    d.text((MARGE + 90, 390), str(s.get("numero", "")), font=police("Bold", 104),
           fill=t["sur_accent"], anchor="mm")
    empiler(d, [
        bloc(s.get("titre"), "Bold", 80, 1.12, t["titre"], 40),
        bloc(s.get("texte"), "Regular", 42, 1.38, t["texte"]),
    ], 560, H - 200)


def m_liste(img, d, t, s):
    haut = 260
    if s.get("etiquette"):
        haut = pastille(d, MARGE, 230, s["etiquette"], t) + 50
    blocs = [bloc(s.get("titre"), "Bold", 76, 1.12, t["titre"], 56)]
    for point in s.get("points", []):
        blocs.append(bloc(point, "Regular", 40, 1.32, t["texte"], 28,
                          puce=True, couleur_puce=t["accent"]))
    empiler(d, blocs, haut, H - 200)


def m_question(img, d, t, s):
    bas = empiler(d, [
        bloc(s.get("titre"), "Bold", 88, 1.12, t["titre"], 40),
        bloc(s.get("texte"), "Medium", 44, 1.3, t["texte"]),
    ], 260, H - 340, centre=True, milieu=True)
    if s.get("bouton"):
        pastille(d, 0, bas + 50, s["bouton"], t, centre=True)


MODELES = {"affiche": m_affiche, "couverture": m_couverture, "etape": m_etape,
           "liste": m_liste, "question": m_question}


def generer(chemin_json):
    with open(chemin_json, encoding="utf-8") as f:
        post = json.load(f)
    dossier = os.path.dirname(os.path.abspath(chemin_json))
    sorties = []
    for i, s in enumerate(post.get("images", []), start=1):
        modele = s.get("modele", "affiche")
        if modele not in MODELES:
            erreur(f"modèle inconnu « {modele} » (possibles : {', '.join(MODELES)}).")
        t = THEMES.get(s.get("theme", "clair"))
        if not t:
            erreur(f"thème inconnu « {s.get('theme')} » (possibles : {', '.join(THEMES)}).")
        img = Image.new("RGB", (W, H), t["fond"])
        d = ImageDraw.Draw(img)
        cadre(img, d, t)
        MODELES[modele](img, d, t, s)
        nom = s.get("fichier", f"{i}.jpg")
        chemin = os.path.join(dossier, nom)
        img.save(chemin, quality=92, optimize=True)
        sorties.append(chemin)
        print("Image :", os.path.relpath(chemin))
    if sorties:  # planche d'aperçu, hors du dépôt
        petites = [Image.open(p).resize((360, 450)) for p in sorties]
        planche = Image.new("RGB", (360 * len(petites) + 10 * (len(petites) - 1), 450), BLANC)
        for i, p in enumerate(petites):
            planche.paste(p, (i * 370, 0))
        apercu = os.path.join(tempfile.gettempdir(), f"apercu_{os.path.basename(dossier)}.jpg")
        planche.save(apercu, quality=85)
        print("Aperçu :", apercu)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        erreur("indique le fichier post.json. Exemple : python3 outils/visuels.py posts/2026-10-16/post.json")
    for chemin in sys.argv[1:]:
        generer(chemin)
