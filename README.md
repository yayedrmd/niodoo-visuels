# Visuels Niodoo

Images des publications Facebook et Instagram de Niodoo. Elles sont publiées
automatiquement via Metricool, qui vient les chercher dans ce dépôt.

**Ne supprime pas et ne renomme pas les images d'un post programmé** :
Metricool en a besoin jusqu'à la publication.

## Organisation

- `posts/AAAA-MM-JJ/post.json` : une publication (date, réseaux, légende, contenu des images)
- `posts/AAAA-MM-JJ/1.jpg, 2.jpg…` : les images générées (1080 x 1350)
- `outils/visuels.py` : le générateur d'images aux couleurs de Niodoo

## Générer les images d'une publication

```
python3 outils/visuels.py posts/2026-10-16/post.json
```

Modèles : `affiche`, `couverture`, `etape`, `liste`, `question`.
Thèmes : `clair` (fond beige) et `fonce` (fond vert olive).
Le détail des champs est en haut de `outils/visuels.py`.

Pas d'emoji ni de flèche dans le texte des images (la police ne les affiche pas).
Pour utiliser le vrai logo à la place du dessin, dépose-le dans `outils/logo.png`
(image carrée, fond transparent).
