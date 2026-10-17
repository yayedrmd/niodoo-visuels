from PIL import Image, ImageDraw, ImageFont

P = "/home/claude/yayedrmd/niodoo-visuels/outils/polices/"
LOGO = "/home/claude/yayedrmd/niodoo-visuels/marque/avatar-niodoo.png"
OUT = "/home/claude/stories/out/"
OLIVE = (79, 90, 63)
GREIGE = (237, 234, 224)
SABLE = (226, 223, 210)
ENCRE = (34, 38, 29)
BLANC = (255, 255, 255)
W, H = 1080, 1920


def f(w, s):
    return ImageFont.truetype(P + f"Manrope-{w}.ttf", s)


def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def header(im, d, dark=False):
    logo = Image.open(LOGO).resize((110, 110))
    m = Image.new("L", (110, 110), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 109, 109), fill=255)
    im.paste(logo, (90, 120), m)
    d.text((222, 175), "NIODOO", font=f("ExtraBold", 44), fill=BLANC if dark else OLIVE, anchor="lm")


def footer(d, dark=False):
    fg, bg = (OLIVE, GREIGE) if dark else (GREIGE, OLIVE)
    d.rounded_rectangle((300, 1700, 780, 1800), 50, fill=bg)
    d.text((540, 1750), "niodoo.net", font=f("Bold", 46), fill=fg, anchor="mm")


def cover(name, letter, title):
    im = Image.new("RGB", (W, H), OLIVE)
    d = ImageDraw.Draw(im)
    d.text((540, 300), "NIODOO", font=f("ExtraBold", 50), fill=SABLE, anchor="mm")
    d.text((540, 960), letter, font=f("ExtraBold", 620), fill=BLANC, anchor="mm")
    d.text((540, 1620), title, font=f("Bold", 72), fill=GREIGE, anchor="mm")
    im.save(OUT + name)


def slide(name, title, items=None, intro=None, outro=None, numbered=False, cols=1, item_size=48, dark=False):
    bg, fg, accent = (OLIVE, BLANC, SABLE) if dark else (GREIGE, ENCRE, OLIVE)
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    header(im, d, dark)
    y = 330
    ft = f("ExtraBold", 84)
    for line in wrap(d, title, ft, 900):
        d.text((90, y), line, font=ft, fill=accent)
        y += 100
    y += 40
    fb = f("Medium", 48)
    if intro:
        for line in wrap(d, intro, fb, 900):
            d.text((90, y), line, font=fb, fill=fg)
            y += 66
        y += 40
    if items:
        fi = f("SemiBold", item_size)
        if cols == 1:
            for i, it in enumerate(items, 1):
                if numbered:
                    d.ellipse((90, y, 160, y + 70), fill=accent)
                    d.text((125, y + 35), str(i), font=f("ExtraBold", 40), fill=bg, anchor="mm")
                else:
                    d.ellipse((105, y + 22, 135, y + 52), fill=accent)
                lines = wrap(d, it, fi, 740)
                for k, line in enumerate(lines):
                    d.text((190, y + 8 + k * (item_size + 18)), line, font=fi, fill=fg)
                y += max(90, len(lines) * (item_size + 18) + 40)
        else:
            per = (len(items) + cols - 1) // cols
            colw = 900 // cols
            for i, it in enumerate(items):
                c, r = divmod(i, per)
                d.text((90 + c * colw, y + r * (item_size + 22)), it, font=fi, fill=fg)
            y += per * (item_size + 22) + 30
    if outro:
        fo = f("Bold", 46)
        for line in wrap(d, outro, fo, 900):
            d.text((90, y), line, font=fo, fill=accent)
            y += 64
    assert y < 1680, (name, y)
    footer(d, dark)
    im.save(OUT + name)


import os
os.makedirs(OUT, exist_ok=True)

# N - Niodoo
cover("N1.png", "N", "Niodoo")
slide("N2.png", "Nous, c'est Niodoo",
      intro="Tu as de la place dans ta valise ? Quelqu'un a un colis à envoyer ? Nous vous mettons en relation.",
      outro="Envoyez loin, dépensez moins.")
slide("N3.png", "Comment ça marche", numbered=True, items=[
    "Le voyageur publie son trajet et fixe son prix au kilo.",
    "L'expéditeur publie son colis ou écrit à un voyageur.",
    "Vous vous mettez d'accord dans la conversation.",
    "Photo du colis au départ, code secret à l'arrivée."])

# I - Inscription
cover("I1.png", "I", "Inscription")
slide("I2.png", "Inscris-toi en 2 minutes", numbered=True, items=[
    "Va sur niodoo.net",
    "Crée ton compte, c'est gratuit",
    "Publie ton trajet ou ton colis",
    "Discute et mets-toi d'accord"],
    outro="Inscription, publication et discussion gratuites.")

# O - Opportunités
cover("O1a.png", "O", "Opportunités")
slide("O2a.png", "Tu voyages ? Rentabilise ton voyage", items=[
    "Tes kilos libres peuvent payer une partie de ton billet",
    "Tu fixes ton prix au kilo",
    "Tu choisis les colis que tu acceptes, photo à l'appui",
    "Ton profil vérifié rassure tes clients"])
slide("O3a.png", "Tu envoies un colis ?", items=[
    "Des voyageurs à l'identité vérifiée",
    "Un prix que tu négocies directement",
    "Une photo du colis au départ",
    "Un suivi jusqu'à l'arrivée"])
slide("O4a.png", "Tu reçois un colis ?", items=[
    "Tu sais où il en est à chaque étape",
    "Tu le récupères avec ton code secret",
    "Remise en main propre"])

# D - Destinations
cover("D1.png", "D", "Destinations")
slide("D2.png", "Afrique de l'Ouest", cols=2, item_size=44, items=[
    "Sénégal", "Mali", "Côte d'Ivoire", "Guinée", "Guinée-Bissau", "Gambie", "Mauritanie", "Burkina Faso",
    "Niger", "Bénin", "Togo", "Ghana", "Nigeria", "Sierra Leone", "Liberia", "Cap-Vert"],
    outro="31 pays d'Afrique disponibles sur Niodoo.")
slide("D3.png", "Le reste de l'Afrique", cols=2, item_size=44, items=[
    "Cameroun", "Gabon", "Congo", "RD Congo", "Centrafrique", "Tchad", "Maroc", "Algérie",
    "Tunisie", "Libye", "Kenya", "Éthiopie", "Rwanda", "Afrique du Sud", "Madagascar"],
    outro="Un trajet s'ouvre dès qu'un voyageur le publie.")
slide("D4.png", "Toute l'Europe", cols=3, item_size=33, items=[
    "France", "Belgique", "Suisse", "Luxembourg", "Monaco", "Espagne", "Portugal", "Italie", "Malte",
    "Allemagne", "Autriche", "Pays-Bas", "Royaume-Uni", "Irlande", "Danemark", "Suède", "Norvège",
    "Finlande", "Islande", "Estonie", "Lettonie", "Lituanie", "Pologne", "Tchéquie", "Slovaquie",
    "Hongrie", "Slovénie", "Croatie", "Bosnie", "Serbie", "Monténégro", "Kosovo", "Albanie",
    "Macédoine du N.", "Grèce", "Chypre", "Bulgarie", "Roumanie", "Moldavie", "Ukraine", "Biélorussie", "Russie"],
    outro="Plus de 70 pays, d'Europe et d'Afrique.")

# O - Options
cover("O1b.png", "O", "Options")
slide("O2b.png", "Bientôt sur Niodoo", dark=True, items=[
    "Des points relais dans plusieurs pays, pour déposer et retirer tes colis",
    "La livraison à domicile, jusqu'à la porte du destinataire"],
    outro="Abonne-toi pour être prévenu en premier.")

# O - On répond
cover("O1c.png", "O", "On répond")
slide("O2c.png", "Qui transporte mon colis ?",
      intro="Un voyageur qui a fait vérifier son identité avant de publier son trajet. Il voit la photo de ton colis avant d'accepter.")
slide("O3c.png", "Comment fonctionne le prix ?",
      intro="C'est le voyageur qui fixe son prix au kilo. Comme sur Vinted, tu peux proposer un prix dans la conversation : il accepte ou fait une contre-proposition.")
slide("O4c.png", "Quels colis puis-je envoyer ?",
      intro="Presque tout, sauf :", items=[
          "Argent liquide", "Médicaments", "Liquides", "Produits périssables", "Produits dangereux", "Contrefaçons"],
      outro="La liste complète est sur le site.")
slide("O5c.png", "Et l'application ?",
      intro="L'application iPhone arrive dans quelques semaines. En attendant, tout se fait sur niodoo.net, depuis ton téléphone ou ton ordinateur.")
print("ok")
