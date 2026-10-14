#!/usr/bin/env python3
"""Visuels Niodoo : génère des images 1080x1350 aux couleurs du site niodoo.net.

Usage :
    python3 outils/visuels.py posts/2026-10-16/post.json
    python3 outils/visuels.py --marque          # avatar + couverture Facebook dans marque/

Le fichier JSON contient une liste "images". Chaque image est enregistrée dans le
même dossier que le JSON (1.jpg, 2.jpg...). Le script affiche aussi le chemin d'une
planche d'aperçu pour vérifier le rendu avant publication.

Identité reprise du site (dépôt du site, packages/ui) :
- le logo : le N tracé d'un seul trait avec un anneau à chaque bout, géométrie exacte
  de packages/ui/src/brand.ts, et le mot NIODOO en capitales espacées ;
- la police : Manrope (800 aux titres, 400 au texte), fournie dans outils/polices ;
- les couleurs : olive #4f5a3f, greige #edeae0, texte #22261d, blanc.

Modèles : affiche, couverture, etape, liste, question
Thèmes  : clair (fond greige), fonce (fond olive)

Champs par modèle :
    affiche    : photo, focus, etiquette, titre, accroche, texte, slogan, centrer
    couverture : photo, focus, etiquette, titre, accroche
    etape      : photo, focus, numero, titre, texte
    liste      : etiquette, titre, points (liste de phrases)
    question   : titre, texte, bouton

"photo" est le nom d'un fichier de outils/photos (sans .jpg), par exemple
"voyageur-aeroport". "focus" place le cadrage, par exemple "50% 40%".

Pas d'emoji ni de flèche dans le texte des images : la police ne les affiche pas,
le script s'arrête avec un message si besoin.
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
PHOTOS = os.path.join(ICI, "photos")
W, H = 1080, 1350
MARGE = 72
LARG = W - 2 * MARGE

OLIVE = (79, 90, 63)        # #4f5a3f, la couleur de marque du site
GREIGE = (237, 234, 224)    # #edeae0, le fond du site
SABLE = (226, 223, 210)     # #e2dfd2, les surfaces du site
ENCRE = (34, 38, 29)        # #22261d, le texte du site
BLANC = (255, 255, 255)

THEMES = {
    "clair": {"fond": GREIGE, "titre": ENCRE, "texte": OLIVE, "accent": OLIVE,
              "sur_accent": BLANC, "logo": OLIVE},
    "fonce": {"fond": OLIVE, "titre": BLANC, "texte": GREIGE, "accent": GREIGE,
              "sur_accent": OLIVE, "logo": BLANC},
}

GRAISSES = {"Regular", "Medium", "SemiBold", "Bold", "ExtraBold"}
PIED_GAUCHE = "niodoo.net"
PIED_DROITE = "@niodoo_officiel"

# Le signe Niodoo, relevé sur la planche du porteur (dépôt du site,
# packages/ui/src/brand.ts). On ne le redessine pas à l'œil.
SIGNE_BOITE = (143.5, 217.0)
SIGNE_TRAIT = 21.0
SIGNE_DEBUT = (31.5, 161.5)
SIGNE_COURBE = ((31.5, 80.0), (31.5, 36.0), (112.0, 177.0), (112.0, 137.0))
SIGNE_FIN = (112.0, 58.5)
SIGNE_ANNEAUX = ((31.5, 185.5, 23.0, 17.0), (112.0, 31.5, 23.0, 17.0))
# Le verrou (signe + mot), relevé sur la même planche.
MOT_HAUTEUR_SIGNE_EM = 2.33
MOT_ECART_EM = 0.82
MOT_INTERLETTRAGE_EM = 0.11
# La pastille (avatar, icône) : signe blanc à 56 % du côté.
PASTILLE_SIGNE = 0.56


def erreur(message):
    sys.exit("ERREUR : " + message)


# --------------------------------------------------------------------------- polices

_polices, _caracteres = {}, {}


def chemin_police(graisse):
    if graisse not in GRAISSES:
        erreur(f"graisse inconnue « {graisse} ».")
    chemin = os.path.join(ICI, "polices", f"Manrope-{graisse}.ttf")
    if not os.path.exists(chemin):
        erreur(f"police introuvable : {chemin}")
    return chemin


def police(graisse, taille):
    cle = (graisse, int(taille))
    if cle not in _polices:
        _polices[cle] = ImageFont.truetype(chemin_police(graisse), int(taille))
    return _polices[cle]


def preparer(texte, graisse):
    """Typographie française (espaces insécables) et refus des caractères absents."""
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


# --------------------------------------------------------------------------- logo

def signe(hauteur, couleur):
    """Le signe Niodoo en RGBA, à la hauteur demandée (en pixels)."""
    ss = 4  # sur-échantillonnage, pour des bords nets
    s = hauteur * ss / SIGNE_BOITE[1]
    m = 2 * ss
    larg, haut = int(SIGNE_BOITE[0] * s) + 2 * m, int(SIGNE_BOITE[1] * s) + 2 * m
    masque = Image.new("L", (larg, haut), 0)
    d = ImageDraw.Draw(masque)

    def p(x, y):
        return (m + x * s, m + y * s)

    p0, p1, p2, p3 = SIGNE_COURBE
    points = [p(*SIGNE_DEBUT), p(*p0)]
    for i in range(1, 401):
        t = i / 400
        a, b, c, e = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        points.append(p(a * p0[0] + b * p1[0] + c * p2[0] + e * p3[0],
                        a * p0[1] + b * p1[1] + c * p2[1] + e * p3[1]))
    points.append(p(*SIGNE_FIN))
    # Le trait est peint au pinceau rond, pas à pas : bords nets dans la courbe et
    # bouts arrondis, comme le stroke-linecap="round" du fichier source.
    r = SIGNE_TRAIT * s / 2
    pas = max(1.0, r / 10)
    for (xa, ya), (xb, yb) in zip(points, points[1:]):
        n = max(1, int(((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5 / pas))
        for k in range(n + 1):
            x, y = xa + (xb - xa) * k / n, ya + (yb - ya) * k / n
            d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    for cx, cy, r, trait in SIGNE_ANNEAUX:
        x, y = p(cx, cy)
        rr = (r + trait / 2) * s
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=255, width=round(trait * s))
    masque = masque.resize((round(larg / ss), round(haut / ss)), Image.LANCZOS)
    sortie = Image.new("RGBA", masque.size, couleur + (255,))
    sortie.putalpha(masque)
    return sortie, round(m / ss)


def verrou(img, x, y, hauteur, couleur):
    """Le verrou complet : le signe puis le mot NIODOO. (x, y) = coin haut gauche du signe."""
    image_signe, marge = signe(hauteur, couleur)
    img.alpha_composite(image_signe, (int(x - marge), int(y - marge))) if img.mode == "RGBA" \
        else img.paste(image_signe, (int(x - marge), int(y - marge)), image_signe)
    taille = hauteur / MOT_HAUTEUR_SIGNE_EM
    f = police("ExtraBold", round(taille))
    d = ImageDraw.Draw(img)
    tx = x + hauteur * SIGNE_BOITE[0] / SIGNE_BOITE[1] + MOT_ECART_EM * taille
    ligne_de_base = y + hauteur / 2 + 0.36 * taille  # capitales centrées sur le signe
    for lettre in "NIODOO":
        d.text((tx, ligne_de_base), lettre, font=f, fill=couleur, anchor="ls")
        tx += d.textlength(lettre, font=f) + MOT_INTERLETTRAGE_EM * taille
    return tx


def pastille(cote, fond=OLIVE, trait=BLANC):
    """L'avatar : le signe blanc centré sur un carré olive (les réseaux le rognent en rond)."""
    img = Image.new("RGB", (cote, cote), fond)
    hauteur = cote * PASTILLE_SIGNE
    image_signe, marge = signe(hauteur, trait)
    largeur = hauteur * SIGNE_BOITE[0] / SIGNE_BOITE[1]
    img.paste(image_signe, (round((cote - largeur) / 2 - marge), round((cote - hauteur) / 2 - marge)),
              image_signe)
    return img


# --------------------------------------------------------------------------- texte

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
                    cy = y + int(f.size * 0.62)
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


def bloc(texte, graisse, taille, interligne, couleur, ecart=0, **autres):
    return dict(texte=texte, graisse=graisse, taille=taille, interligne=interligne,
                couleur=couleur, ecart=ecart, **autres)


def etiquette(d, x, y, texte, t, centre=False):
    texte = preparer(texte, "Bold")
    f = police("Bold", 28)
    largeur = d.textlength(texte, font=f) + 56
    if centre:
        x = (W - largeur) / 2
    d.rounded_rectangle([x, y, x + largeur, y + 56], 28, fill=t["accent"])
    d.text((x + 28, y + 28), texte, font=f, fill=t["sur_accent"], anchor="lm")
    return y + 56


# --------------------------------------------------------------------------- cadre

def photo(img, nom, hauteur, focus="50% 50%"):
    """Pose une photo de outils/photos en haut de l'image, recadrée sur `focus`."""
    chemin = os.path.join(PHOTOS, f"{nom}.jpg")
    if not os.path.exists(chemin):
        disponibles = ", ".join(sorted(f[:-4] for f in os.listdir(PHOTOS) if f.endswith(".jpg")))
        erreur(f"photo « {nom} » introuvable. Photos disponibles : {disponibles}")
    ph = Image.open(chemin).convert("RGB")
    r = max(W / ph.width, hauteur / ph.height)
    nl, nh = round(ph.width * r), round(ph.height * r)
    ph = ph.resize((nl, nh), Image.LANCZOS)
    fx, fy = (float(v.strip("%")) / 100 for v in focus.split())
    x0 = min(max(round(fx * nl - W / 2), 0), nl - W)
    y0 = min(max(round(fy * nh - hauteur / 2), 0), nh - hauteur)
    img.paste(ph.crop((x0, y0, x0 + W, y0 + hauteur)), (0, 0))
    # Un voile léger en haut, pour que le logo blanc se lise sur toutes les photos.
    voile = Image.new("L", (1, 260))
    for y in range(260):
        voile.putpixel((0, y), int(120 * (1 - y / 260) ** 1.7))
    img.paste(Image.new("RGB", (W, 260), (18, 20, 15)), (0, 0), voile.resize((W, 260)))


def cadre(img, d, t, sur_photo=False):
    verrou(img, MARGE, 64, 62, BLANC if sur_photo else t["logo"])
    f = police("SemiBold", 26)
    d.text((MARGE, H - 74), PIED_GAUCHE, font=f, fill=t["texte"], anchor="ls")
    d.text((W - MARGE, H - 74), PIED_DROITE, font=f, fill=t["texte"], anchor="rs")


def slogan(d, texte, t, y_ligne=H - 150):
    d.line([MARGE, y_ligne, W - MARGE, y_ligne], fill=t["accent"], width=2)
    empiler(d, [bloc(texte, "ExtraBold", 40, 1.2, t["accent"])], y_ligne - 70, y_ligne - 12)


# --------------------------------------------------------------------------- modèles

def m_affiche(img, d, t, s):
    if s.get("photo"):
        haut = 700 + 48
    else:
        haut = 236
    if s.get("etiquette"):
        haut = etiquette(d, MARGE, haut, s["etiquette"], t) + 40
    bas = H - 250 if s.get("slogan") else H - 140
    taille_titre = 64 if s.get("photo") else 84
    empiler(d, [
        bloc(s.get("titre"), "ExtraBold", taille_titre, 1.1, t["titre"], 30),
        bloc(s.get("accroche"), "SemiBold", 46, 1.22, t["texte"], 28),
        bloc(s.get("texte"), "Regular", 36, 1.4, t["texte"]),
    ], haut, bas, milieu=bool(s.get("centrer")))
    if s.get("slogan"):
        slogan(d, s["slogan"], t)


def m_couverture(img, d, t, s):
    haut = 820 + 40 if s.get("photo") else 236
    if s.get("etiquette"):
        haut = etiquette(d, MARGE, haut, s["etiquette"], t) + 40
    taille_titre = 66 if s.get("photo") else 96
    empiler(d, [
        bloc(s.get("titre"), "ExtraBold", taille_titre, 1.08, t["titre"], 26),
        bloc(s.get("accroche"), "SemiBold", 40, 1.25, t["texte"]),
    ], haut, H - 140, milieu=True)


def m_etape(img, d, t, s):
    if s.get("photo"):
        cy = 700  # la pastille chevauche le bas de la photo
    else:
        cy = 390
    d.ellipse([MARGE - 6, cy - 96, MARGE + 186, cy + 96], fill=t["fond"])
    d.ellipse([MARGE, cy - 90, MARGE + 180, cy + 90], fill=t["accent"])
    d.text((MARGE + 90, cy), str(s.get("numero", "")), font=police("ExtraBold", 100),
           fill=t["sur_accent"], anchor="mm")
    empiler(d, [
        bloc(s.get("titre"), "ExtraBold", 70, 1.1, t["titre"], 28),
        bloc(s.get("texte"), "Regular", 38, 1.4, t["texte"]),
    ], cy + 130, H - 140)


def m_liste(img, d, t, s):
    haut = 236
    if s.get("etiquette"):
        haut = etiquette(d, MARGE, haut, s["etiquette"], t) + 44
    blocs = [bloc(s.get("titre"), "ExtraBold", 76, 1.1, t["titre"], 52)]
    for point in s.get("points", []):
        blocs.append(bloc(point, "Regular", 40, 1.32, t["texte"], 28,
                          puce=True, couleur_puce=t["accent"]))
    empiler(d, blocs, haut, H - 140)


def m_question(img, d, t, s):
    bas = empiler(d, [
        bloc(s.get("titre"), "ExtraBold", 88, 1.1, t["titre"], 36),
        bloc(s.get("texte"), "SemiBold", 42, 1.3, t["texte"]),
    ], 236, H - 300, centre=True, milieu=True)
    if s.get("bouton"):
        etiquette(d, 0, bas + 44, s["bouton"], t, centre=True)


MODELES = {"affiche": m_affiche, "couverture": m_couverture, "etape": m_etape,
           "liste": m_liste, "question": m_question}
HAUTEUR_PHOTO = {"affiche": 700, "couverture": 820, "etape": 700}


def image(s):
    modele = s.get("modele", "affiche")
    if modele not in MODELES:
        erreur(f"modèle inconnu « {modele} » (possibles : {', '.join(MODELES)}).")
    t = THEMES.get(s.get("theme", "clair"))
    if not t:
        erreur(f"thème inconnu « {s.get('theme')} » (possibles : {', '.join(THEMES)}).")
    if s.get("photo") and modele not in HAUTEUR_PHOTO:
        erreur(f"le modèle « {modele} » ne prend pas de photo.")
    img = Image.new("RGB", (W, H), t["fond"])
    if s.get("photo"):
        photo(img, s["photo"], HAUTEUR_PHOTO[modele], s.get("focus", "50% 50%"))
    d = ImageDraw.Draw(img)
    cadre(img, d, t, sur_photo=bool(s.get("photo")))
    MODELES[modele](img, d, t, s)
    return img


def generer(chemin_json):
    with open(chemin_json, encoding="utf-8") as f:
        post = json.load(f)
    dossier = os.path.dirname(os.path.abspath(chemin_json))
    sorties = []
    for i, s in enumerate(post.get("images", []), start=1):
        nom = s.get("fichier", f"{i}.jpg")
        chemin = os.path.join(dossier, nom)
        image(s).save(chemin, quality=92, optimize=True)
        sorties.append(chemin)
        print("Image :", os.path.relpath(chemin))
    if sorties:  # planche d'aperçu, hors du dépôt
        petites = [Image.open(p).resize((360, 450)) for p in sorties]
        planche = Image.new("RGB", (370 * len(petites) - 10, 450), BLANC)
        for i, p in enumerate(petites):
            planche.paste(p, (i * 370, 0))
        apercu = os.path.join(tempfile.gettempdir(), f"apercu_{os.path.basename(dossier)}.jpg")
        planche.save(apercu, quality=85)
        print("Aperçu :", apercu)


# --------------------------------------------------------------------------- marque

def couverture_facebook(chemin):
    """Couverture de Page Facebook 1640x624. Le contenu reste au centre, seule zone
    visible à la fois sur ordinateur et sur téléphone."""
    L, Hc = 1640, 624
    img = Image.new("RGB", (L, Hc), OLIVE)
    ph = Image.open(os.path.join(PHOTOS, "envoi-en-famille.jpg")).convert("RGB")
    r = max(L / ph.width, Hc / ph.height)
    ph = ph.resize((round(ph.width * r), round(ph.height * r)), Image.LANCZOS)
    y0 = min(max(round(0.38 * ph.height - Hc / 2), 0), ph.height - Hc)
    x0 = (ph.width - L) // 2
    img.paste(ph.crop((x0, y0, x0 + L, y0 + Hc)), (0, 0))
    img = Image.blend(img, Image.new("RGB", (L, Hc), OLIVE), 0.80)
    d = ImageDraw.Draw(img)
    hauteur = 120
    taille = hauteur / MOT_HAUTEUR_SIGNE_EM
    f = police("ExtraBold", round(taille))
    largeur_mot = sum(d.textlength(c, font=f) for c in "NIODOO") + 5 * MOT_INTERLETTRAGE_EM * taille
    largeur = hauteur * SIGNE_BOITE[0] / SIGNE_BOITE[1] + MOT_ECART_EM * taille + largeur_mot
    verrou(img, (L - largeur) / 2, 150, hauteur, BLANC)
    d = ImageDraw.Draw(img)
    titre = preparer("Envoyez loin, dépensez moins.", "ExtraBold")
    d.text((L / 2, 352), titre, font=police("ExtraBold", 58), fill=BLANC, anchor="ms")
    sous = preparer("Vos colis entre l'Europe et l'Afrique, avec des voyageurs vérifiés.", "SemiBold")
    d.text((L / 2, 418), sous, font=police("SemiBold", 32), fill=GREIGE, anchor="ms")
    d.text((L / 2, 480), "niodoo.net", font=police("Bold", 30), fill=BLANC, anchor="ms")
    img.save(chemin, quality=93, optimize=True)
    print("Couverture Facebook :", os.path.relpath(chemin))


def marque():
    dossier = os.path.join(os.path.dirname(ICI), "marque")
    os.makedirs(dossier, exist_ok=True)
    pastille(1080).save(os.path.join(dossier, "avatar-niodoo.png"))
    print("Avatar :", os.path.relpath(os.path.join(dossier, "avatar-niodoo.png")))
    couverture_facebook(os.path.join(dossier, "couverture-facebook.jpg"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        erreur("indique le fichier post.json. Exemple : python3 outils/visuels.py posts/2026-10-16/post.json")
    if sys.argv[1] == "--marque":
        marque()
    else:
        for chemin in sys.argv[1:]:
            generer(chemin)
