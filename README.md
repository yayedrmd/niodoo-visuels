# Visuels Niodoo

Images des publications Facebook et Instagram de Niodoo. Elles sont publiées
automatiquement via Metricool, qui vient les chercher dans ce dépôt.

**Ne supprime pas et ne renomme pas les images d'un post programmé** :
Metricool en a besoin jusqu'à la publication.

## Organisation

- `posts/AAAA-MM-JJ/post.json` : une publication (date, réseaux, légende, contenu des images)
- `posts/AAAA-MM-JJ/1.jpg, 2.jpg…` : les images générées (1080 x 1350)
- `marque/` : l'avatar (logo officiel) et la couverture de la Page Facebook
- `outils/visuels.py` : le générateur d'images
- `outils/photos/` : les photos du site niodoo.net (images générées par IA)
- `outils/polices/` : Manrope, la police du site (licence libre OFL)

## Identité

Tout est repris du site niodoo.net : le logo (le N tracé d'un seul trait, un anneau
à chaque bout, géométrie exacte de la planche de marque), la police Manrope et les
couleurs (olive `#4f5a3f`, greige `#edeae0`, texte `#22261d`).

## Générer les images

```
python3 outils/visuels.py posts/2026-10-16/post.json   # les images d'une publication
python3 outils/visuels.py --marque                     # avatar et couverture Facebook
```

Modèles : `affiche`, `couverture`, `etape`, `liste`, `question`.
Thèmes : `clair` (fond greige) et `fonce` (fond olive).
Les modèles `affiche`, `couverture` et `etape` acceptent une photo de `outils/photos`.
Le détail des champs est en haut de `outils/visuels.py`.

Pas d'emoji ni de flèche dans le texte des images (la police ne les affiche pas).
Les posts qui utilisent les photos sont déclarés « générés par IA » sur Instagram.
