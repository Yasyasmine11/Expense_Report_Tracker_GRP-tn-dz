# -*- coding: utf-8 -*-
"""
Generate comprehensive personal learning guide PDF for Expense Tracker project.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.platypus import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# ── Color palette ────────────────────────────────────────────────────────────
DARK_BLUE    = HexColor("#232F3E")
ORANGE       = HexColor("#FF9900")
WHITE        = HexColor("#FFFFFF")
LIGHT_GREY   = HexColor("#F8F9FA")
DARK_GREY    = HexColor("#2D3748")
MED_GREY     = HexColor("#718096")
CODE_BG      = HexColor("#1E2A3A")
CODE_FG      = HexColor("#E2E8F0")
YELLOW_BG    = HexColor("#FFFBEB")
YELLOW_BORDER= HexColor("#F59E0B")
GREEN_BG     = HexColor("#F0FFF4")
GREEN_BORDER = HexColor("#38A169")
SECTION_BLUE = HexColor("#1A365D")
BANNER_BG    = HexColor("#232F3E")

OUTPUT_PATH = (
    r"C:\Users\user\OneDrive\Bureau\estiam aws expense"
    r"\Expense_Report_Tracker_GRP-tn-dz\docs\explication_personnelle.pdf"
)

PAGE_W, PAGE_H = A4  # 595.27 x 841.89 pts


# ── Custom flowable: coloured left-border box ────────────────────────────────
class BorderBox(Flowable):
    """A box with a solid left border and background fill."""
    def __init__(self, content_paragraphs, bg_color, border_color,
                 border_width=4, padding=10, width=None):
        super().__init__()
        self.paragraphs     = content_paragraphs
        self.bg_color       = bg_color
        self.border_color   = border_color
        self.border_width   = border_width
        self.padding        = padding
        self._width         = width

    def wrap(self, avail_width, avail_height):
        self.avail_width = self._width or avail_width
        inner = self.avail_width - self.border_width - 2 * self.padding
        total_h = self.padding
        for p in self.paragraphs:
            w, h = p.wrap(inner, avail_height)
            total_h += h + 4
        total_h += self.padding
        self._height = total_h
        return (self.avail_width, self._height)

    def draw(self):
        c = self.canv
        w = self.avail_width
        h = self._height
        # background
        c.setFillColor(self.bg_color)
        c.rect(0, 0, w, h, stroke=0, fill=1)
        # left border
        c.setFillColor(self.border_color)
        c.rect(0, 0, self.border_width, h, stroke=0, fill=1)
        # draw paragraphs
        inner = w - self.border_width - 2 * self.padding
        y = h - self.padding
        for p in self.paragraphs:
            pw, ph = p.wrap(inner, h)
            y -= ph
            p.drawOn(c, self.border_width + self.padding, y)
            y -= 4
        c.setFillColor(colors.black)


# ── Custom flowable: chapter banner ─────────────────────────────────────────
class ChapterBanner(Flowable):
    def __init__(self, text, width=None):
        super().__init__()
        self._text  = text
        self._width = width

    def wrap(self, avail_width, avail_height):
        self.avail_width = self._width or avail_width
        self._height = 42
        return (self.avail_width, self._height)

    def draw(self):
        c = self.canv
        w = self.avail_width
        h = self._height
        # dark-blue background
        c.setFillColor(BANNER_BG)
        c.roundRect(0, 0, w, h, 6, stroke=0, fill=1)
        # orange text
        c.setFillColor(ORANGE)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(14, 13, self._text)
        c.setFillColor(colors.black)


# ── Custom flowable: code block ──────────────────────────────────────────────
class CodeBlock(Flowable):
    def __init__(self, code_text, width=None):
        super().__init__()
        self.code_text = code_text
        self._width    = width

    def wrap(self, avail_width, avail_height):
        self.avail_width = self._width or avail_width
        lines = self.code_text.split("\n")
        font_size   = 8
        line_height = font_size * 1.35
        self._height = len(lines) * line_height + 20
        self._lines  = lines
        return (self.avail_width, self._height)

    def draw(self):
        c = self.canv
        w = self.avail_width
        h = self._height
        # background
        c.setFillColor(CODE_BG)
        c.roundRect(0, 0, w, h, 4, stroke=0, fill=1)
        # code text
        c.setFillColor(CODE_FG)
        c.setFont("Courier", 8)
        line_height = 8 * 1.35
        y = h - 14
        for line in self._lines:
            c.drawString(10, y, line)
            y -= line_height
        c.setFillColor(colors.black)


# ── Page-number canvas callback ───────────────────────────────────────────────
def add_page_number(canvas, doc):
    canvas.saveState()
    page_num = canvas.getPageNumber()
    if page_num == 1:
        canvas.restoreState()
        return
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MED_GREY)
    canvas.drawRightString(
        PAGE_W - 20*mm, 10*mm,
        "Page %d" % page_num
    )
    canvas.drawString(
        20*mm, 10*mm,
        "Mon Projet Expense Tracker - Guide d'apprentissage"
    )
    canvas.restoreState()


# ── Style factory ─────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    styles = {}

    styles["body"] = ParagraphStyle(
        "body",
        parent=base["Normal"],
        fontSize=10,
        leading=15,
        textColor=DARK_GREY,
        spaceBefore=4,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
    )

    styles["section"] = ParagraphStyle(
        "section",
        parent=base["Normal"],
        fontSize=12,
        leading=16,
        textColor=SECTION_BLUE,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=6,
    )

    styles["toc_title"] = ParagraphStyle(
        "toc_title",
        parent=base["Normal"],
        fontSize=22,
        leading=28,
        textColor=DARK_BLUE,
        fontName="Helvetica-Bold",
        spaceBefore=20,
        spaceAfter=14,
        alignment=TA_CENTER,
    )

    styles["toc_item"] = ParagraphStyle(
        "toc_item",
        parent=base["Normal"],
        fontSize=10,
        leading=18,
        textColor=DARK_GREY,
        leftIndent=8,
    )

    styles["toc_item_bold"] = ParagraphStyle(
        "toc_item_bold",
        parent=base["Normal"],
        fontSize=10,
        leading=18,
        textColor=DARK_BLUE,
        fontName="Helvetica-Bold",
        leftIndent=0,
        spaceBefore=4,
    )

    styles["analogy_body"] = ParagraphStyle(
        "analogy_body",
        parent=base["Normal"],
        fontSize=10,
        leading=14,
        textColor=DARK_GREY,
    )

    styles["analogy_label"] = ParagraphStyle(
        "analogy_label",
        parent=base["Normal"],
        fontSize=10,
        leading=14,
        textColor=HexColor("#92400E"),
        fontName="Helvetica-Bold",
    )

    styles["key_label"] = ParagraphStyle(
        "key_label",
        parent=base["Normal"],
        fontSize=10,
        leading=14,
        textColor=HexColor("#276749"),
        fontName="Helvetica-Bold",
    )

    styles["key_body"] = ParagraphStyle(
        "key_body",
        parent=base["Normal"],
        fontSize=10,
        leading=14,
        textColor=DARK_GREY,
    )

    return styles


# ── Helper builders ───────────────────────────────────────────────────────────
def S(styles, key="body"):
    return styles[key]


def body(styles, text):
    return Paragraph(text, S(styles, "body"))


def section(styles, text):
    return Paragraph(text, S(styles, "section"))


def spacer(h=6):
    return Spacer(1, h)


def analogy_box(styles, text):
    """Yellow box with orange left border."""
    paras = [
        Paragraph("Analogie :", S(styles, "analogy_label")),
        Paragraph(text, S(styles, "analogy_body")),
    ]
    return BorderBox(paras, YELLOW_BG, YELLOW_BORDER, border_width=5, padding=10)


def key_box(styles, text):
    """Green box with green left border."""
    paras = [
        Paragraph("Points cles :", S(styles, "key_label")),
        Paragraph(text, S(styles, "key_body")),
    ]
    return BorderBox(paras, GREEN_BG, GREEN_BORDER, border_width=5, padding=10)


def code_block(code_text):
    return CodeBlock(code_text)


def chapter_banner(text):
    return ChapterBanner(text)


# ─────────────────────────────────────────────────────────────────────────────
# COVER PAGE  (drawn directly on canvas via onFirstPage callback)
# ─────────────────────────────────────────────────────────────────────────────
class CoverPage(Flowable):
    """Full-page cover drawn directly on the canvas."""
    def wrap(self, avail_width, avail_height):
        # Claim the full page frame
        return (avail_width, avail_height)

    def draw(self):
        c = self.canv
        w = PAGE_W
        h = PAGE_H

        # --- dark-blue background (absolute coords from bottom-left) ---
        # We draw relative to the frame origin; use absolute via canvas transform
        c.saveState()
        # Translate to absolute page origin (undo frame margins)
        c.translate(-20*mm, -15*mm)
        c.setFillColor(DARK_BLUE)
        c.rect(0, 0, w, h, stroke=0, fill=1)

        # Decorative orange horizontal bar (top third)
        c.setFillColor(ORANGE)
        c.rect(0, h * 0.62, w, 6, stroke=0, fill=1)
        c.rect(0, h * 0.38, w, 3, stroke=0, fill=1)

        # Main title
        c.setFillColor(ORANGE)
        c.setFont("Helvetica-Bold", 32)
        title = "Mon Projet Expense Tracker"
        c.drawCentredString(w / 2, h * 0.68, title)

        # Subtitle
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(w / 2, h * 0.58, "Tout Comprendre de A a Z")

        # Sub-subtitle line 1
        c.setFont("Helvetica", 13)
        c.drawCentredString(w / 2, h * 0.51, "Guide personnel d'apprentissage")
        # Sub-subtitle line 2
        c.drawCentredString(w / 2, h * 0.47, "Architecture AWS, Code C#, Interface MAUI")

        # Footer
        c.setFillColor(ORANGE)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(w / 2, h * 0.12, "ESTIAM Paris - Master 2 - 2026")

        # Small decorative dots
        c.setFillColor(ORANGE)
        for i, dot_x in enumerate([w*0.3, w*0.5, w*0.7]):
            c.circle(dot_x, h * 0.3, 4, stroke=0, fill=1)

        c.restoreState()


def build_cover():
    """Return flowables for the cover page."""
    return [CoverPage(), PageBreak()]


# ─────────────────────────────────────────────────────────────────────────────
# TABLE OF CONTENTS
# ─────────────────────────────────────────────────────────────────────────────
def build_toc(styles):
    story = []
    story.append(Paragraph("Table des matieres", S(styles, "toc_title")))
    story.append(HRFlowable(width="100%", thickness=2, color=ORANGE, spaceAfter=12))

    chapters = [
        ("Chapitre 1",  "Vue d'ensemble - C'est quoi ce projet ?"),
        ("Chapitre 2",  "L'Architecture - Comment les pieces s'assemblent"),
        ("Chapitre 3",  "AWS Lambda - Le Coeur du Backend"),
        ("Chapitre 4",  "Amazon DynamoDB - La Base de Donnees NoSQL"),
        ("Chapitre 5",  "Amazon API Gateway - La Porte d'Entree"),
        ("Chapitre 6",  "Amazon Cognito - L'Authentification"),
        ("Chapitre 7",  "Amazon S3 - Le Stockage des Recus"),
        ("Chapitre 8",  "IAM - La Securite des Permissions"),
        ("Chapitre 9",  "Le Frontend - .NET MAUI et C#"),
        ("Chapitre 10", "Structure du Code Frontend - Les Services et Pages"),
        ("Chapitre 11", "Le Monitoring - CloudWatch"),
        ("Chapitre 12", "Les Bugs qu'on a Rencontres et Comment on les a Resolus"),
        ("Chapitre 13", "Glossaire - Les Termes Importants"),
    ]

    for num, title in chapters:
        row_data = [
            Paragraph(num, S(styles, "toc_item_bold")),
            Paragraph(title, S(styles, "toc_item")),
        ]
        t = Table([row_data], colWidths=[80, PAGE_W - 40*mm - 80])
        t.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(t)
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#E2E8F0"), spaceAfter=2))

    story.append(PageBreak())
    return story


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 1
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter1(styles):
    s = []
    s.append(chapter_banner("Chapitre 1 - Vue d'ensemble - C'est quoi ce projet ?"))
    s.append(spacer(10))

    s.append(section(styles, "1.1 Le probleme que l'on resout"))
    s.append(body(styles, (
        "Dans beaucoup d'entreprises, quand un employe fait une depense professionnelle "
        "(repas avec un client, billet de train, achat de materiel), il doit en demander "
        "le remboursement. Avant le numerique, ca se faisait avec des formulaires papier, "
        "des signatures, des classeurs. Long, fastidieux, et on perd souvent les recus."
    )))
    s.append(body(styles, (
        "Notre projet <b>Expense Tracker</b> resout ce probleme : c'est une application "
        "complete qui permet de creer, soumettre et approuver des notes de frais de facon "
        "numerique, securisee, et tracable."
    )))
    s.append(spacer(8))

    s.append(section(styles, "1.2 Les deux utilisateurs"))
    s.append(body(styles, "Notre application a deux types d'utilisateurs avec des roles differents :"))
    s.append(body(styles, (
        "<b>Alice (Employe)</b> peut : Creer une note de frais (montant, categorie, description), "
        "Joindre un recu photo, Soumettre sa note pour approbation, Voir l'historique de ses notes et leur statut."
    )))
    s.append(body(styles, (
        "<b>Bob (Finance Manager)</b> peut : Voir toutes les notes soumises par tous les employes, "
        "Approuver une note (l'employe sera rembourse), Rejeter une note avec un motif, "
        "Consulter l'historique complet."
    )))
    s.append(spacer(6))
    s.append(analogy_box(styles, (
        "Imagine une feuille de remboursement papier que tu remplis et deposes dans la boite "
        "de la comptabilite. Notre app fait exactement ca, mais en numerique : plus de papier "
        "perdu, tout est trace, et le manager peut approuver depuis n'importe ou."
    )))
    s.append(spacer(10))

    s.append(section(styles, "1.3 Le cycle de vie d'une note de frais"))
    s.append(body(styles, "Chaque note de frais passe par des etats bien definis, comme un colis qu'on suit :"))
    s.append(body(styles, (
        "<b>DRAFT (Brouillon)</b> : Alice vient de creer la note, elle n'est pas encore soumise. "
        "Elle peut encore la modifier.<br/>"
        "<b>SUBMITTED (Soumise)</b> : Alice a clique 'Soumettre'. La note attend l'approbation de Bob.<br/>"
        "<b>APPROVED (Approuvee)</b> : Bob a approuve. Alice sera remboursee.<br/>"
        "<b>REJECTED (Rejetee)</b> : Bob a rejete avec un motif. Alice peut corriger et re-soumettre."
    )))
    s.append(body(styles, (
        "Ces transitions sont controlees cote serveur (dans nos Lambda functions). Le client ne peut "
        "pas tricher - on ne peut pas approuver une note qui n'est pas en statut SUBMITTED, par exemple."
    )))
    s.append(spacer(8))

    s.append(section(styles, "1.4 Pourquoi AWS et pas un serveur classique ?"))
    s.append(body(styles, "On aurait pu faire cette app avec un serveur Apache + PHP + MySQL comme en cours. Mais on a choisi AWS pour plusieurs raisons :"))
    s.append(body(styles, (
        "<b>Pas de serveur a gerer :</b> Avec AWS Lambda, on n'a pas de serveur qui tourne 24h/24. "
        "Le code s'execute seulement quand quelqu'un fait une requete.<br/>"
        "<b>Paiement a l'usage :</b> On paye seulement les executions Lambda, pas un serveur qui tourne "
        "meme quand personne l'utilise.<br/>"
        "<b>Scalabilite automatique :</b> Si 1000 employes soumettent des notes en meme temps, AWS s'adapte automatiquement.<br/>"
        "<b>Securite integree :</b> Cognito, IAM, HTTPS - tout est deja la."
    )))
    s.append(spacer(8))
    s.append(key_box(styles, (
        "Notre app remplace le processus papier de notes de frais. "
        "Deux roles : employe (Alice) et finance manager (Bob). "
        "Cycle de vie : DRAFT -> SUBMITTED -> APPROVED/REJECTED. "
        "AWS offre scalabilite, securite et paiement a l'usage."
    )))
    s.append(PageBreak())
    return s


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 2
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter2(styles):
    s = []
    s.append(chapter_banner("Chapitre 2 - L'Architecture - Comment les pieces s'assemblent"))
    s.append(spacer(10))

    s.append(section(styles, "2.1 La vue d'ensemble"))
    s.append(body(styles, (
        "Notre application est composee de plusieurs services AWS qui communiquent entre eux. "
        "Voici le chemin complet d'une requete :"
    )))
    s.append(spacer(4))
    s.append(code_block(
        "[Application MAUI Windows/Android]\n"
        "           |\n"
        "           | HTTPS + Token JWT\n"
        "           v\n"
        "[Amazon API Gateway]  <-- verifie le token avec Cognito\n"
        "           |\n"
        "           | appelle la bonne fonction\n"
        "           v\n"
        "[AWS Lambda (C# .NET 8)]  <-- execute la logique metier\n"
        "     |           |\n"
        "     v           v\n"
        "[DynamoDB]    [Amazon S3]\n"
        "(donnees)    (photos recus)\n\n"
        "[Amazon Cognito] --> fournit les tokens JWT\n"
        "[IAM Role] --> donne les permissions a Lambda"
    ))
    s.append(spacer(10))

    s.append(section(styles, "2.2 Ce qui se passe quand Alice clique 'Creer une note'"))
    s.append(body(styles, "Voici le chemin complet, etape par etape :"))
    steps = [
        "1. Alice remplit le formulaire dans l'app MAUI (montant: 50 euros, categorie: REPAS, description: Dejeuner client)",
        "2. L'app envoie une requete HTTP POST vers API Gateway avec le token JWT dans le header Authorization",
        "3. API Gateway recoit la requete. Il extrait le token JWT et le verifie aupres de Cognito",
        "4. Cognito confirme : 'Oui, c'est le token d'Alice, elle est dans le groupe employees'",
        "5. API Gateway transmet la requete a la fonction Lambda CreateExpense avec les informations d'Alice",
        "6. Lambda cree un item dans DynamoDB avec PK=USER#alice-uuid, SK=EXPENSE#nouveau-uuid, status=DRAFT",
        "7. Lambda repond : {\"expenseId\": \"abc123\", \"status\": \"DRAFT\"}",
        "8. API Gateway renvoie cette reponse a l'app MAUI",
        "9. L'app affiche 'Note creee avec succes !'",
    ]
    for step in steps:
        s.append(body(styles, step))
    s.append(body(styles, "<i>Tout ca se passe en moins d'une seconde.</i>"))
    s.append(spacer(10))

    s.append(section(styles, "2.3 Le concept Serverless explique simplement"))
    s.append(analogy_box(styles, (
        "Taxi vs Voiture personnelle : Un serveur classique, c'est comme avoir une voiture : "
        "elle prend de la place dans le garage, elle consomme meme quand tu ne l'utilises pas, "
        "tu dois faire la revision toi-meme. AWS Lambda c'est comme Uber : tu commandes une "
        "voiture seulement quand tu en as besoin, tu payes uniquement le trajet, et tu n'as "
        "pas a t'occuper de la maintenance."
    )))
    s.append(spacer(8))
    s.append(key_box(styles, (
        "L'architecture suit le chemin : MAUI -> API Gateway -> Lambda -> DynamoDB/S3. "
        "API Gateway verifie le token JWT avant chaque appel Lambda. "
        "Serverless = pas de serveur a gerer, paiement a l'usage uniquement."
    )))
    s.append(PageBreak())
    return s


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 3
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter3(styles):
    s = []
    s.append(chapter_banner("Chapitre 3 - AWS Lambda - Le Coeur du Backend"))
    s.append(spacer(10))

    s.append(section(styles, "3.1 C'est quoi une fonction Lambda ?"))
    s.append(analogy_box(styles, (
        "La machine distributrice : Imagine une machine distributrice. Elle ne fait rien tant "
        "que personne n'appuie sur un bouton. Quand tu appuies sur 'Coca', elle execute une "
        "action precise (distribue un Coca) et s'arrete. C'est exactement Lambda : dormant "
        "par defaut, il s'execute quand il recoit une requete, fait son travail, et s'arrete."
    )))
    s.append(spacer(6))
    s.append(body(styles, (
        "Une Lambda function, c'est un morceau de code qui s'execute en reponse a un evenement. "
        "Dans notre cas, l'evenement est une requete HTTP qui arrive sur API Gateway. Lambda "
        "recoit la requete, execute le code C#, et renvoie une reponse."
    )))
    s.append(spacer(8))

    s.append(section(styles, "3.2 Nos 7 fonctions et leur role"))
    functions = [
        ("CreateExpense", "Creer une note de frais",
         "Recoit : montant, categorie, description + token JWT. "
         "Fait : extrait l'identite d'Alice, cree un item DynamoDB avec status DRAFT. "
         "Repond : {\"expenseId\": \"abc123\", \"status\": \"DRAFT\"}"),
        ("GetExpenses", "Lister les notes",
         "Recoit : token JWT. "
         "Fait : si employe, retourne ses notes. Si finance manager, retourne toutes les notes SUBMITTED. "
         "Repond : {\"expenses\": [...liste...]}"),
        ("SubmitExpense", "Soumettre une note",
         "Recoit : expenseId dans l'URL + token JWT. "
         "Fait : verifie que la note appartient a Alice, change status de DRAFT a SUBMITTED. "
         "Repond : {\"status\": \"SUBMITTED\"}"),
        ("ApproveExpense", "Approuver une note",
         "Recoit : expenseId + userId + token JWT de Bob. "
         "Fait : VERIFIE que Bob est dans le groupe 'finance', verifie SUBMITTED, change en APPROVED. "
         "Repond : {\"status\": \"APPROVED\"}"),
        ("RejectExpense", "Rejeter une note",
         "Recoit : expenseId + userId + justification + token JWT de Bob. "
         "Fait : verification RBAC, change en REJECTED, sauvegarde la justification. "
         "Repond : {\"status\": \"REJECTED\"}"),
        ("GetUploadUrl", "Obtenir une URL d'upload",
         "Recoit : expenseId + token JWT. "
         "Fait : verifie que la note appartient a Alice, genere une URL S3 pre-signee valide 10 minutes. "
         "Repond : {\"uploadUrl\": \"https://s3.amazonaws.com/...?X-Amz-Signature=...\"}"),
        ("GetExpenseById", "Obtenir une note precise",
         "Recoit : expenseId dans l'URL + token JWT. "
         "Fait : recupere l'item DynamoDB specifique, verifie les permissions. "
         "Repond : la note complete"),
    ]
    for fn_name, fn_title, fn_desc in functions:
        s.append(body(styles, f"<b>{fn_name}</b> - {fn_title}"))
        s.append(body(styles, fn_desc))
        s.append(spacer(4))

    s.append(section(styles, "3.3 Le langage C# et .NET 8"))
    s.append(body(styles, (
        "On a code le backend en C# avec .NET 8. "
        "<b>C# est un langage fortement type</b> : ca veut dire que le compilateur detecte les erreurs avant "
        "l'execution. Si tu passes un texte a la place d'un nombre, ca ne compile pas. "
        "<b>.NET 8 est supporte nativement par AWS Lambda</b> : Amazon fournit un runtime .NET 8 optimise pour Lambda. "
        "On utilise les memes competences cote frontend (MAUI) et backend (Lambda) : un seul langage pour tout le projet."
    )))
    s.append(spacer(8))

    s.append(section(styles, "3.4 Structure d'une fonction Lambda"))
    s.append(code_block(
        "public class Function\n"
        "{\n"
        "    private readonly IAmazonDynamoDB _dynamo;\n"
        "    private readonly string _tableName;\n\n"
        "    // Constructeur : initialise les connexions AWS\n"
        "    public Function()\n"
        "    {\n"
        "        _dynamo = new AmazonDynamoDBClient();\n"
        "        _tableName = Environment.GetEnvironmentVariable(\"TABLE_NAME\");\n"
        "    }\n\n"
        "    // Handler : point d'entree appele par AWS Lambda\n"
        "    public async Task<APIGatewayProxyResponse> FunctionHandler(\n"
        "        APIGatewayProxyRequest request, ILambdaContext context)\n"
        "    {\n"
        "        var claims = request.RequestContext.Authorizer.Claims;\n"
        "        var userId = claims[\"sub\"]; // identifiant unique Cognito\n\n"
        "        var dto = JsonConvert.DeserializeObject<CreateExpenseDto>(request.Body);\n\n"
        "        await _dynamo.PutItemAsync(new PutItemRequest {\n"
        "            TableName = _tableName,\n"
        "            Item = new Dictionary<string, AttributeValue> {\n"
        "                [\"PK\"] = new() { S = \"USER#\" + userId },\n"
        "                [\"SK\"] = new() { S = \"EXPENSE#\" + Guid.NewGuid() },\n"
        "                [\"status\"] = new() { S = \"DRAFT\" }\n"
        "            }\n"
        "        });\n\n"
        "        return new APIGatewayProxyResponse {\n"
        "            StatusCode = 201,\n"
        "            Body = \"{\\\"message\\\": \\\"Expense created\\\"}\"\n"
        "        };\n"
        "    }\n"
        "}"
    ))
    s.append(spacer(8))

    s.append(section(styles, "3.5 Deployer une Lambda"))
    s.append(code_block(
        "# Se placer dans le dossier de la Lambda\n"
        "cd backend/lambdas/createExpense\n\n"
        "# Deployer sur AWS\n"
        "dotnet lambda deploy-function CreateExpense\n\n"
        "# L'outil va :\n"
        "# 1. Compiler le code C#\n"
        "# 2. Creer un fichier ZIP avec le binaire\n"
        "# 3. Uploader le ZIP sur AWS\n"
        "# 4. Mettre a jour la fonction Lambda"
    ))
    s.append(spacer(8))
    s.append(key_box(styles, (
        "Lambda = code qui s'execute seulement quand necessaire. "
        "On a 7 fonctions Lambda, chacune avec une responsabilite precise. "
        "Code en C# .NET 8, deploye avec 'dotnet lambda deploy-function'. "
        "Chaque Lambda lit les claims JWT pour connaitre l'identite et le role de l'utilisateur."
    )))
    s.append(PageBreak())
    return s


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 4
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter4(styles):
    s = []
    s.append(chapter_banner("Chapitre 4 - Amazon DynamoDB - La Base de Donnees NoSQL"))
    s.append(spacer(10))

    s.append(section(styles, "4.1 SQL vs NoSQL - La difference fondamentale"))
    s.append(analogy_box(styles, (
        "Feuille Excel vs Dictionnaire : Une base SQL (MySQL, PostgreSQL), c'est comme une feuille "
        "Excel : des colonnes fixes, des lignes, des relations entre tables. DynamoDB (NoSQL), c'est "
        "comme un dictionnaire : chaque entree a une cle unique, et la valeur peut avoir n'importe "
        "quelle forme. Pas de schema fixe, pas de colonnes obligatoires."
    )))
    s.append(spacer(6))
    s.append(body(styles, "Dans une base SQL, si tu veux stocker une note de frais, tu definis d'abord la structure :"))
    s.append(code_block(
        "-- SQL classique\n"
        "CREATE TABLE expenses (\n"
        "    id VARCHAR(36) PRIMARY KEY,\n"
        "    user_id VARCHAR(36),\n"
        "    amount DECIMAL(10,2),\n"
        "    status VARCHAR(20),\n"
        "    created_at TIMESTAMP\n"
        ");"
    ))
    s.append(body(styles, (
        "En DynamoDB, pas de schema : tu envoies directement un objet JSON et il est stocke tel quel. "
        "La flexibilite est totale, mais ca demande de reflechir differemment."
    )))
    s.append(spacer(8))

    s.append(section(styles, "4.2 Notre table ExpenseReports"))
    s.append(body(styles, (
        "Notre table utilise le pattern <b>Single-Table Design</b> : une seule table stocke tous les types "
        "de donnees. La cle est composee de deux parties :<br/>"
        "<b>PK (Partition Key)</b> : identifie le 'groupe' de donnees. Pour nous : USER#alice-uuid<br/>"
        "<b>SK (Sort Key)</b> : identifie l'element dans le groupe. Pour nous : EXPENSE#expense-uuid"
    )))
    s.append(code_block(
        "{\n"
        "    \"PK\": \"USER#a1b2c3d4-uuid-alice\",\n"
        "    \"SK\": \"EXPENSE#x9y8z7-uuid-note\",\n"
        "    \"expenseId\": \"x9y8z7-uuid-note\",\n"
        "    \"userId\": \"a1b2c3d4-uuid-alice\",\n"
        "    \"userEmail\": \"alice@test.com\",\n"
        "    \"amount\": 50.00,\n"
        "    \"category\": \"REPAS\",\n"
        "    \"description\": \"Dejeuner client\",\n"
        "    \"status\": \"SUBMITTED\",\n"
        "    \"StatusGSI_PK\": \"STATUS#SUBMITTED\",\n"
        "    \"createdAt\": \"2026-05-15T14:30:00Z\",\n"
        "    \"updatedAt\": \"2026-05-15T15:00:00Z\"\n"
        "}"
    ))
    s.append(spacer(8))

    s.append(section(styles, "4.3 Le GSI (Global Secondary Index) - StatusIndex"))
    s.append(body(styles, (
        "Probleme : comment Bob (finance manager) peut voir toutes les notes SUBMITTED, venant de tous "
        "les employes ? Avec notre structure PK=USER#..., on ne peut requeter que les notes d'un seul "
        "utilisateur a la fois."
    )))
    s.append(body(styles, (
        "Solution : le <b>GSI</b> (Global Secondary Index). C'est un index supplementaire sur la table, "
        "avec une cle differente. Notre GSI 'StatusIndex' : Hash Key = StatusGSI_PK (ex: 'STATUS#SUBMITTED'), "
        "Range Key = SK. Quand Alice soumet sa note, on met a jour StatusGSI_PK = 'STATUS#SUBMITTED'. Bob peut "
        "alors requeter le GSI et recuperer TOUTES les notes soumises, de tous les employes."
    )))
    s.append(code_block(
        "// Requete du manager : toutes les notes SUBMITTED\n"
        "var request = new QueryRequest {\n"
        "    TableName = \"ExpenseReports\",\n"
        "    IndexName = \"StatusIndex\",\n"
        "    KeyConditionExpression = \"StatusGSI_PK = :status\",\n"
        "    ExpressionAttributeValues = new Dictionary<string, AttributeValue> {\n"
        "        [\":status\"] = new AttributeValue { S = \"STATUS#SUBMITTED\" }\n"
        "    }\n"
        "};"
    ))
    s.append(spacer(8))

    s.append(section(styles, "4.4 Query vs GetItem vs Scan"))
    s.append(body(styles, (
        "<b>GetItem</b> : recupere UN item precis par sa cle (PK + SK). Ultra rapide, latence inferieure a 5ms. "
        "On l'utilise pour GetExpenseById.<br/>"
        "<b>Query</b> : recupere PLUSIEURS items avec la meme PK. Rapide, indexe. On l'utilise pour GetExpenses "
        "(toutes les notes d'Alice).<br/>"
        "<b>Scan</b> : parcourt TOUTE la table. Lent et cher, a eviter absolument en production. On ne l'utilise JAMAIS."
    )))
    s.append(spacer(8))
    s.append(key_box(styles, (
        "DynamoDB est NoSQL : pas de schema fixe, flexibilite totale. "
        "Notre table utilise PK=USER#userId et SK=EXPENSE#expenseId. "
        "Le GSI StatusIndex permet au manager de trouver toutes les notes SUBMITTED sans scanner la table. "
        "Toujours utiliser GetItem ou Query, jamais Scan."
    )))
    s.append(PageBreak())
    return s


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 5
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter5(styles):
    s = []
    s.append(chapter_banner("Chapitre 5 - Amazon API Gateway - La Porte d'Entree"))
    s.append(spacer(10))

    s.append(section(styles, "5.1 C'est quoi une API REST ?"))
    s.append(analogy_box(styles, (
        "Le menu d'un restaurant : Une API REST, c'est comme le menu d'un restaurant. Tu (le client) "
        "regardes le menu, tu choisis un plat (endpoint), tu passes ta commande (requete HTTP), et le "
        "serveur (API Gateway) transmet a la cuisine (Lambda) qui prepare et renvoie le plat (reponse JSON)."
    )))
    s.append(spacer(6))
    s.append(body(styles, (
        "REST signifie Representational State Transfer. C'est un style d'architecture pour les APIs web. "
        "Chaque action est definie par : une URL (l'endpoint) et un verbe HTTP (GET, POST, PUT, DELETE)."
    )))
    s.append(spacer(8))

    s.append(section(styles, "5.2 Les verbes HTTP expliques"))
    s.append(body(styles, (
        "<b>GET</b> : lire des donnees. Exemple : GET /expenses -> lire toutes mes notes de frais<br/>"
        "<b>POST</b> : creer quelque chose. Exemple : POST /expenses -> creer une nouvelle note<br/>"
        "<b>PUT</b> : modifier quelque chose. Exemple : PUT /expenses/abc/submit -> soumettre la note abc<br/>"
        "<b>DELETE</b> : supprimer. On n'en a pas dans notre projet."
    )))
    s.append(spacer(8))

    s.append(section(styles, "5.3 Nos 7 endpoints"))
    s.append(code_block(
        "GET    /expenses                     -> GetExpenses (liste)\n"
        "POST   /expenses                     -> CreateExpense (creation)\n"
        "GET    /expenses/{expenseId}         -> GetExpenseById (detail)\n"
        "POST   /expenses/{expenseId}/submit  -> SubmitExpense\n"
        "POST   /expenses/{expenseId}/approve -> ApproveExpense\n"
        "POST   /expenses/{expenseId}/reject  -> RejectExpense\n"
        "GET    /expenses/{expenseId}/upload-url -> GetUploadUrl\n\n"
        "Base URL: https://rwfqaety92.execute-api.eu-west-3.amazonaws.com/prod/"
    ))
    s.append(spacer(8))

    s.append(section(styles, "5.4 Le bug de l'URL que l'on a eu"))
    s.append(body(styles, "On a eu un bug critique au debut : toutes les requetes retournaient 403 Forbidden. La cause etait subtile."))
    s.append(code_block(
        "// MAUVAIS : BaseAddress sans '/' final\n"
        "_http = new HttpClient {\n"
        "    BaseAddress = new Uri(\"https://xxx.execute-api.eu-west-3.amazonaws.com/prod\")\n"
        "};\n"
        "// _http.GetStringAsync(\"/expenses\")\n"
        "// -> https://xxx.execute-api.eu-west-3.amazonaws.com/expenses  <- FAUX !\n\n"
        "// CORRECT : BaseAddress avec '/' final + chemin sans '/'\n"
        "_http = new HttpClient {\n"
        "    BaseAddress = new Uri(\"https://xxx.execute-api.eu-west-3.amazonaws.com/prod/\")\n"
        "};\n"
        "_http.GetStringAsync(\"expenses\"); // -> /prod/expenses CORRECT"
    ))
    s.append(spacer(8))

    s.append(section(styles, "5.5 Le Cognito Authorizer"))
    s.append(body(styles, "Chaque requete vers notre API doit contenir un token JWT valide dans le header HTTP. API Gateway verifie ce token automatiquement avant d'appeler Lambda."))
    s.append(code_block(
        "// Dans l'app MAUI, on attache le token a chaque requete\n"
        "_http.DefaultRequestHeaders.Authorization =\n"
        "    new AuthenticationHeaderValue(\"Bearer\", idToken);\n\n"
        "// Ce que API Gateway recoit :\n"
        "// Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...\n\n"
        "// API Gateway verifie : signature valide ? token expire ?\n"
        "// Si OK : transmet la requete a Lambda avec les claims du token\n"
        "// Si KO : retourne 401 Unauthorized"
    ))
    s.append(spacer(8))
    s.append(key_box(styles, (
        "API Gateway est le point d'entree unique de notre application. "
        "Les verbes HTTP definissent l'action : GET=lire, POST=creer. "
        "L'URL doit avoir un '/' final avec HttpClient. "
        "Le Cognito Authorizer verifie le JWT avant chaque appel Lambda."
    )))
    s.append(PageBreak())
    return s


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 6
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter6(styles):
    s = []
    s.append(chapter_banner("Chapitre 6 - Amazon Cognito - L'Authentification"))
    s.append(spacer(10))

    s.append(section(styles, "6.1 Le probleme de l'identite"))
    s.append(analogy_box(styles, (
        "Le badge d'entreprise : Quand tu entres dans une entreprise avec un badge, la securite "
        "verifie ton badge, voit ton nom et ton departement, et t'autorise a acceder a certaines zones. "
        "Cognito fait la meme chose pour notre app : il emet des 'badges numeriques' (tokens JWT) "
        "qui prouvent qui tu es et quel est ton role."
    )))
    s.append(spacer(8))

    s.append(section(styles, "6.2 Le User Pool"))
    s.append(body(styles, (
        "Le User Pool Cognito est la liste de tous les utilisateurs de notre application. "
        "C'est lui qui gere : l'inscription et la connexion, la verification des mots de passe, les groupes d'utilisateurs.<br/><br/>"
        "Dans notre projet : User Pool ID = eu-west-3_IFDSxyrQK (region Paris).<br/>"
        "Nos utilisateurs de test : alice@test.com (groupe employees), bob@test.com (groupe finance)."
    )))
    s.append(spacer(8))

    s.append(section(styles, "6.3 Le JWT (JSON Web Token)"))
    s.append(body(styles, (
        "Quand Alice se connecte, Cognito lui donne deux tokens JWT : IdToken et AccessToken. "
        "On utilise l'IdToken car il contient les informations dont on a besoin."
        " Un JWT est compose de 3 parties separees par des points :"
    )))
    s.append(code_block(
        "// Structure d'un JWT\n"
        "eyJhbGciOiJSUzI1NiJ9     <- Header (encode en Base64)\n"
        ".\n"
        "eyJzdWIiOiJhMWIyYzMiLCJlbWFpbCI6ImFsaWNlQHRlc3QuY29tIn0\n"
        "                          <- Payload (encode en Base64)\n"
        ".\n"
        "SflKxwRJSMeKKF2QT4fwpM   <- Signature (verifie l'authenticite)\n\n"
        "// Le Payload decode contient :\n"
        "{\n"
        "    \"sub\": \"a1b2c3d4-uuid-alice\",\n"
        "    \"email\": \"alice@test.com\",\n"
        "    \"cognito:groups\": [\"employees\"],\n"
        "    \"exp\": 1747000000\n"
        "}"
    ))
    s.append(spacer(8))

    s.append(section(styles, "6.4 Pourquoi IdToken et pas AccessToken ?"))
    s.append(body(styles, (
        "<b>IdToken</b> : contient sub, email, cognito:groups (les roles). C'est celui que nos Lambda lisent pour le RBAC.<br/>"
        "<b>AccessToken</b> : contient sub et les scopes OAuth, mais PAS cognito:groups (selon la configuration).<br/><br/>"
        "Pour que Bob soit reconnu comme finance manager, Lambda doit lire cognito:groups dans le token. "
        "Donc on envoie l'IdToken."
    )))
    s.append(spacer(8))

    s.append(section(styles, "6.5 Le RBAC dans le code Lambda"))
    s.append(code_block(
        "// Dans chaque Lambda qui necessite un role specifique\n"
        "private static bool IsFinanceManager(IDictionary<string, string> claims)\n"
        "{\n"
        "    if (claims.TryGetValue(\"cognito:groups\", out var groups))\n"
        "        return groups.Contains(\"finance\");\n"
        "    return false;\n"
        "}\n\n"
        "// Utilisation dans ApproveExpense :\n"
        "var claims = request.RequestContext.Authorizer.Claims;\n"
        "if (!IsFinanceManager(claims))\n"
        "{\n"
        "    return new APIGatewayProxyResponse {\n"
        "        StatusCode = 403,\n"
        "        Body = \"{\\\"error\\\": \\\"Only Finance Managers can approve.\\\"}\"\n"
        "    };\n"
        "}"
    ))
    s.append(spacer(8))
    s.append(key_box(styles, (
        "Cognito gere l'authentification et les groupes d'utilisateurs. "
        "Un JWT est un token signe qui prouve l'identite et le role. "
        "On utilise l'IdToken (et non l'AccessToken) car il contient cognito:groups. "
        "Lambda lit le claim cognito:groups pour le RBAC."
    )))
    s.append(PageBreak())
    return s


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 7
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter7(styles):
    s = []
    s.append(chapter_banner("Chapitre 7 - Amazon S3 - Le Stockage des Recus"))
    s.append(spacer(10))

    s.append(section(styles, "7.1 C'est quoi S3 ?"))
    s.append(analogy_box(styles, (
        "Google Drive pour developpeurs : S3 (Simple Storage Service) c'est comme Google Drive, "
        "mais pour les applications. Tu peux y stocker n'importe quel fichier (photos, videos, "
        "documents), y acceder via une URL, et configurer finement les permissions d'acces."
    )))
    s.append(spacer(6))
    s.append(body(styles, (
        "Notre bucket S3 : <b>expense-tracker-receipts-706922781773</b>. "
        "Il stocke les photos de recus des employes sous la structure : receipts/{userId}/{expenseId}.jpg"
    )))
    s.append(spacer(8))

    s.append(section(styles, "7.2 La Pre-Signed URL - Comment ca marche ?"))
    s.append(body(styles, (
        "Probleme : si on envoie la photo via Lambda, le fichier doit transiter par Lambda -> lent et couteux.<br/>"
        "Solution : la <b>pre-signed URL</b>. Une pre-signed URL est une URL temporaire generee par Lambda "
        "(qui a les permissions S3) et donnee directement a l'app. L'app peut alors uploader la photo "
        "DIRECTEMENT sur S3, sans passer par Lambda."
    )))
    s.append(code_block(
        "// Lambda genere l'URL temporaire\n"
        "var presignRequest = new GetPreSignedUrlRequest\n"
        "{\n"
        "    BucketName  = \"expense-tracker-receipts-706922781773\",\n"
        "    Key         = \"receipts/\" + userId + \"/\" + expenseId + \".jpg\",\n"
        "    Verb        = HttpVerb.PUT,\n"
        "    Expires     = DateTime.UtcNow.AddMinutes(10),\n"
        "    ContentType = \"image/jpeg\"\n"
        "};\n"
        "string uploadUrl = _s3.GetPreSignedURL(presignRequest);\n\n"
        "// L'app MAUI upload directement sur S3\n"
        "await uploadClient.PutAsync(uploadUrl, imageContent);"
    ))
    s.append(spacer(8))

    s.append(section(styles, "7.3 Securite du bucket"))
    s.append(body(styles, (
        "Notre bucket est completement prive. Personne ne peut y acceder directement depuis internet. "
        "Les seuls acces possibles sont : via une pre-signed URL generee par Lambda (valide 10 minutes max), "
        "ou directement par Lambda via son role IAM."
    )))
    s.append(spacer(8))
    s.append(key_box(styles, (
        "S3 stocke les photos de recus. "
        "La pre-signed URL permet a l'app d'uploader directement sur S3 sans passer par Lambda -> plus rapide et moins cher. "
        "Le bucket est prive : acces uniquement via URLs temporaires de 10 minutes."
    )))
    s.append(PageBreak())
    return s


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 8
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter8(styles):
    s = []
    s.append(chapter_banner("Chapitre 8 - IAM - La Securite des Permissions"))
    s.append(spacer(10))

    s.append(section(styles, "8.1 C'est quoi IAM ?"))
    s.append(analogy_box(styles, (
        "Les cles d'un immeuble : IAM (Identity and Access Management) c'est le systeme de cles "
        "et de badges d'un immeuble. Chaque employe a une cle qui lui donne acces uniquement aux "
        "pieces dont il a besoin. Le stagiaire ne peut pas entrer dans la salle serveur. Le directeur "
        "a acces partout. IAM fait la meme chose pour les services AWS."
    )))
    s.append(spacer(8))

    s.append(section(styles, "8.2 Notre role Lambda"))
    s.append(body(styles, (
        "Notre role IAM <b>expense-tracker-lambda-role</b> est attache a toutes nos Lambda functions. "
        "Il leur donne exactement les permissions necessaires, et rien de plus."
    )))
    s.append(code_block(
        "// Permissions accordees au role Lambda\n"
        "Autorisees :\n"
        "  dynamodb:GetItem        -> lire un item\n"
        "  dynamodb:PutItem        -> creer un item\n"
        "  dynamodb:UpdateItem     -> modifier un item\n"
        "  dynamodb:Query          -> requeter la table\n"
        "  s3:GetObject            -> lire un fichier S3\n"
        "  s3:PutObject            -> uploader un fichier S3\n"
        "  logs:CreateLogGroup     -> creer des logs CloudWatch\n"
        "  logs:PutLogEvents       -> ecrire des logs\n\n"
        "Refusees (implicitement tout le reste) :\n"
        "  x  dynamodb:DeleteItem  -> supprimer des items\n"
        "  x  s3:DeleteObject      -> supprimer des fichiers\n"
        "  x  iam:*                -> modifier des permissions\n"
        "  x  ec2:*                -> acceder aux serveurs\n"
        "  x  rds:*                -> acceder aux bases SQL"
    ))
    s.append(spacer(8))
    s.append(key_box(styles, (
        "IAM gere les permissions dans AWS. "
        "Le principe du moindre privilege : donner uniquement les acces necessaires. "
        "Notre Lambda ne peut faire que ce dont elle a besoin, rien de plus."
    )))
    s.append(PageBreak())
    return s


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 9
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter9(styles):
    s = []
    s.append(chapter_banner("Chapitre 9 - Le Frontend - .NET MAUI et C#"))
    s.append(spacer(10))

    s.append(section(styles, "9.1 C'est quoi .NET MAUI ?"))
    s.append(body(styles, (
        "MAUI signifie <b>Multi-platform App UI</b>. C'est un framework Microsoft qui permet de creer "
        "une seule application et de la deployer sur plusieurs plateformes : Windows, Android, iOS, macOS.<br/><br/>"
        "Dans notre projet : on cible Windows (application desktop) et Android (application mobile). "
        "On a une seule base de code C# qui tourne sur les deux."
    )))
    s.append(spacer(8))

    s.append(section(styles, "9.2 Pourquoi MAUI et pas une app web ?"))
    s.append(body(styles, (
        "On aurait pu faire l'interface en React ou Vue.js (JavaScript). On a choisi MAUI parce que :<br/>"
        "- On utilise deja C# pour les Lambda -> meme langage partout<br/>"
        "- Acces natif aux fonctionnalites du telephone (camera pour les recus)<br/>"
        "- Application qui tourne meme hors ligne (mode brouillon)"
    )))
    s.append(spacer(8))

    s.append(section(styles, "9.3 XAML - Le langage de l'interface"))
    s.append(analogy_box(styles, (
        "HTML pour les apps : XAML (eXtensible Application Markup Language) est au frontend MAUI "
        "ce que HTML est aux pages web. C'est un langage XML qui decrit l'interface graphique : "
        "les boutons, les champs de texte, les listes. Le C# gere la logique, le XAML gere l'affichage."
    )))
    s.append(spacer(6))
    s.append(body(styles, "Voici un exemple de notre LoginPage.xaml :"))
    s.append(code_block(
        "<!-- Un champ de saisie email dans XAML -->\n"
        "<Border BackgroundColor=\"#F7FAFC\"\n"
        "        StrokeShape=\"RoundRectangle 8\"\n"
        "        Stroke=\"#CBD5E0\">\n"
        "    <Entry x:Name=\"EmailEntry\"\n"
        "           Placeholder=\"alice@company.com\"\n"
        "           TextColor=\"#1A202C\"\n"
        "           Keyboard=\"Email\"\n"
        "           HeightRequest=\"44\"/>\n"
        "</Border>\n\n"
        "<!-- Un bouton -->\n"
        "<Button Text=\"Se connecter\"\n"
        "        BackgroundColor=\"#FF9900\"\n"
        "        TextColor=\"White\"\n"
        "        Clicked=\"OnLoginClicked\"/>"
    ))
    s.append(spacer(6))
    s.append(body(styles, "Et le code C# correspondant (LoginPage.xaml.cs) :"))
    s.append(code_block(
        "private async void OnLoginClicked(object sender, EventArgs e)\n"
        "{\n"
        "    string email    = EmailEntry.Text.Trim();\n"
        "    string password = PasswordEntry.Text;\n\n"
        "    var result = await _auth.LoginAsync(email, password);\n\n"
        "    if (result.IsFinanceManager)\n"
        "        await Shell.Current.GoToAsync(\"//ManagerPage\");\n"
        "    else\n"
        "        await Shell.Current.GoToAsync(\"//EmployeePage\");\n"
        "}"
    ))
    s.append(spacer(8))

    s.append(section(styles, "9.4 Visual Studio 2026"))
    s.append(body(styles, (
        "Visual Studio est l'IDE qu'on utilise pour developper l'app MAUI. Il fournit : editeur de code "
        "avec completion automatique (IntelliSense), compilateur (transforme le C# en .exe), debugger "
        "(permet de mettre des points d'arret et inspecter les variables), designer XAML (apercu visuel).<br/><br/>"
        "Le raccourci <b>F5</b> fait tout : compile le code, deploie l'app, la lance, et attache le debugger. "
        "Si tu mets un point d'arret dans le code, l'execution se met en pause et tu peux inspecter les variables."
    )))
    s.append(spacer(8))

    s.append(section(styles, "9.5 Le probleme SDK qu'on a eu"))
    s.append(body(styles, (
        "On a eu un probleme : Visual Studio 2026 utilise .NET 10 SDK par defaut, mais le workload MAUI "
        "n'etait installe que sur .NET 9. VS ne reconnaissait pas le projet comme une app.<br/><br/>"
        "Solution : le fichier global.json qui force le SDK 9 :"
    )))
    s.append(code_block(
        "// frontend/global.json\n"
        "{\n"
        "    \"sdk\": {\n"
        "        \"version\": \"9.0.203\",\n"
        "        \"rollForward\": \"latestPatch\"\n"
        "    }\n"
        "}"
    ))
    s.append(spacer(8))
    s.append(key_box(styles, (
        "MAUI = une seule base de code C# pour Windows et Android. "
        "XAML decrit l'interface, C# gere la logique. "
        "Visual Studio compile et lance l'app avec F5. "
        "global.json force la version du SDK .NET."
    )))
    s.append(PageBreak())
    return s


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 10
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter10(styles):
    s = []
    s.append(chapter_banner("Chapitre 10 - Structure du Code Frontend"))
    s.append(spacer(10))

    s.append(section(styles, "10.1 AuthService.cs - La connexion"))
    s.append(body(styles, "Ce service gere tout ce qui touche a l'authentification. Il utilise le SDK AWS Cognito pour .NET."))
    s.append(code_block(
        "public class AuthService\n"
        "{\n"
        "    private static string? _idToken;\n"
        "    private static bool _isFinanceManager;\n\n"
        "    public async Task<LoginResult> LoginAsync(string email, string password)\n"
        "    {\n"
        "        var response = await _cognito.InitiateAuthAsync(new InitiateAuthRequest {\n"
        "            AuthFlow = AuthFlowType.USER_PASSWORD_AUTH,\n"
        "            ClientId = AppConfig.AppClientId,\n"
        "            AuthParameters = new Dictionary<string, string> {\n"
        "                { \"USERNAME\", email },\n"
        "                { \"PASSWORD\", password }\n"
        "            }\n"
        "        });\n\n"
        "        var jwt    = new JwtSecurityTokenHandler()\n"
        "            .ReadJwtToken(response.AuthenticationResult.IdToken);\n"
        "        var groups = jwt.Claims\n"
        "            .Where(c => c.Type == \"cognito:groups\")\n"
        "            .Select(c => c.Value).ToList();\n\n"
        "        _idToken          = response.AuthenticationResult.IdToken;\n"
        "        _isFinanceManager = groups.Contains(\"finance\");\n\n"
        "        return new LoginResult { Success = true, IsFinanceManager = _isFinanceManager };\n"
        "    }\n"
        "}"
    ))
    s.append(spacer(8))

    s.append(section(styles, "10.2 ExpenseService.cs - Les appels API"))
    s.append(body(styles, "Ce service fait tous les appels HTTP vers notre API Gateway. C'est lui qui attache le token JWT a chaque requete."))
    s.append(code_block(
        "public class ExpenseService\n"
        "{\n"
        "    private readonly HttpClient _http;\n\n"
        "    public ExpenseService()\n"
        "    {\n"
        "        // IMPORTANT : le '/' final est obligatoire !\n"
        "        _http = new HttpClient {\n"
        "            BaseAddress = new Uri(\n"
        "                \"https://rwfqaety92.execute-api.eu-west-3.amazonaws.com/prod/\")\n"
        "        };\n"
        "    }\n\n"
        "    private void Auth()\n"
        "    {\n"
        "        var token = AuthService.GetIdToken();\n"
        "        _http.DefaultRequestHeaders.Authorization =\n"
        "            new AuthenticationHeaderValue(\"Bearer\", token);\n"
        "    }\n\n"
        "    public async Task<List<ExpenseReport>> GetMyExpensesAsync()\n"
        "    {\n"
        "        Auth();\n"
        "        var response = await _http.GetStringAsync(\"expenses\");\n"
        "        var json     = JObject.Parse(response);\n"
        "        return json[\"expenses\"]?.ToObject<List<ExpenseReport>>()\n"
        "               ?? new List<ExpenseReport>();\n"
        "    }\n"
        "}"
    ))
    s.append(spacer(8))

    s.append(section(styles, "10.3 Le modele ExpenseReport"))
    s.append(body(styles, "Ce modele C# represente une note de frais. Il a des proprietes 'calculees' qui derivent automatiquement du status :"))
    s.append(code_block(
        "public class ExpenseReport\n"
        "{\n"
        "    public string  ExpenseId   { get; set; } = \"\";\n"
        "    public decimal Amount      { get; set; }\n"
        "    public string  Status      { get; set; } = \"\";\n"
        "    public string  Category    { get; set; } = \"\";\n\n"
        "    // Proprietes calculees pour l'affichage\n"
        "    public string StatusLabel => Status switch {\n"
        "        \"DRAFT\"     => \"Brouillon\",\n"
        "        \"SUBMITTED\" => \"En attente\",\n"
        "        \"APPROVED\"  => \"Approuvee\",\n"
        "        \"REJECTED\"  => \"Rejetee\",\n"
        "        _           => Status\n"
        "    };\n\n"
        "    public bool CanSubmit  => Status == \"DRAFT\" || Status == \"REJECTED\";\n"
        "    public bool CanReview  => Status == \"SUBMITTED\";\n\n"
        "    public string AmountFormatted => \"EUR \" + Amount.ToString(\"F2\");\n"
        "}"
    ))
    s.append(spacer(8))
    s.append(key_box(styles, (
        "AuthService gere la connexion Cognito et stocke l'IdToken. "
        "ExpenseService fait tous les appels HTTP avec le token attache. "
        "Le modele ExpenseReport a des proprietes calculees qui controlent l'affichage selon le statut."
    )))
    s.append(PageBreak())
    return s


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 11
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter11(styles):
    s = []
    s.append(chapter_banner("Chapitre 11 - Le Monitoring - CloudWatch"))
    s.append(spacer(10))

    s.append(section(styles, "11.1 Pourquoi monitorer ?"))
    s.append(analogy_box(styles, (
        "Le tableau de bord d'une voiture : Tu n'attends pas que ta voiture tombe en panne pour regarder "
        "la jauge d'essence. Le tableau de bord te donne des infos en temps reel. CloudWatch est le tableau "
        "de bord de notre infrastructure AWS : invocations Lambda, erreurs, temps de reponse, tout est visible."
    )))
    s.append(spacer(8))

    s.append(section(styles, "11.2 Notre dashboard"))
    s.append(body(styles, (
        "On a cree un dashboard CloudWatch <b>ExpenseTracker-Overview</b> avec 4 graphiques :<br/>"
        "- Lambda Invocations (nombre d'appels par fonction)<br/>"
        "- Lambda Errors (nombre d'erreurs)<br/>"
        "- Lambda Duration (temps d'execution moyen en ms)<br/>"
        "- API Gateway Requests (requetes totales, erreurs 4XX et 5XX)"
    )))
    s.append(spacer(8))

    s.append(section(styles, "11.3 L'alarme Lambda"))
    s.append(body(styles, "On a configure une alarme qui se declenche si plus de 5 erreurs Lambda surviennent en 5 minutes."))
    s.append(code_block(
        "# Configuration de l'alarme (AWS CLI)\n"
        "aws cloudwatch put-metric-alarm \\\n"
        "    --alarm-name \"ExpenseTracker-Lambda-Errors\" \\\n"
        "    --metric-name Errors \\\n"
        "    --namespace AWS/Lambda \\\n"
        "    --threshold 5 \\\n"
        "    --comparison-operator GreaterThanOrEqualToThreshold \\\n"
        "    --period 300 \\\n"
        "    --evaluation-periods 1"
    ))
    s.append(spacer(8))

    s.append(section(styles, "11.4 DynamoDB PITR"))
    s.append(body(styles, (
        "PITR (Point-In-Time Recovery) est la sauvegarde automatique de DynamoDB. Elle conserve un "
        "historique de 35 jours. Si quelqu'un supprime accidentellement des donnees, on peut restaurer "
        "la table a n'importe quel moment dans cette fenetre."
    )))
    s.append(spacer(8))
    s.append(key_box(styles, (
        "CloudWatch surveille l'infrastructure en temps reel. "
        "Notre dashboard montre invocations, erreurs, duree et requetes API. "
        "L'alarme alerte si trop d'erreurs. "
        "DynamoDB PITR permet de restaurer les donnees sur 35 jours."
    )))
    s.append(PageBreak())
    return s


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 12
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter12(styles):
    s = []
    s.append(chapter_banner("Chapitre 12 - Les Bugs Rencontres et Comment on les a Resolus"))
    s.append(spacer(10))

    s.append(body(styles, (
        "Tout projet rencontre des problemes. Voici les principaux bugs qu'on a resolus, "
        "et ce qu'on a appris."
    )))
    s.append(spacer(8))

    s.append(section(styles, "12.1 Bug 1 - Erreur 403 sur tous les appels API"))
    s.append(body(styles, (
        "<b>Symptome :</b> Toutes les requetes vers l'API retournaient '403 Forbidden'. "
        "L'app se lancait, le login fonctionnait, mais impossible de charger les notes de frais.<br/><br/>"
        "<b>Cause :</b> HttpClient avec un BaseAddress sans '/' final."
    )))
    s.append(code_block(
        "// MAUVAIS\n"
        "BaseAddress = \"https://xxx.execute-api.eu-west-3.amazonaws.com/prod\"\n"
        "+ GetStringAsync(\"/expenses\")\n"
        "= https://xxx.execute-api.eu-west-3.amazonaws.com/expenses  <- FAUX !\n\n"
        "// CORRECT\n"
        "BaseAddress = \"https://xxx.execute-api.eu-west-3.amazonaws.com/prod/\"\n"
        "+ GetStringAsync(\"expenses\")\n"
        "= https://xxx.execute-api.eu-west-3.amazonaws.com/prod/expenses  <- OK !"
    ))
    s.append(spacer(8))

    s.append(section(styles, "12.2 Bug 2 - Visual Studio dit 'bibliotheque de classes'"))
    s.append(body(styles, (
        "<b>Symptome :</b> VS refuse de lancer l'app avec l'erreur 'Impossible de demarrer directement "
        "un projet avec un type de sortie de bibliotheque de classes'.<br/><br/>"
        "<b>Cause :</b> VS evalue OutputType avant de charger les targets MAUI."
    )))
    s.append(code_block(
        "<!-- Solution : definir explicitement l'OutputType dans .csproj -->\n"
        "<OutputType\n"
        "    Condition=\"$([MSBuild]::GetTargetPlatformIdentifier('$(TargetFramework)')) == 'windows'\">\n"
        "    WinExe\n"
        "</OutputType>"
    ))
    s.append(spacer(8))

    s.append(section(styles, "12.3 Bug 3 - Mauvaise version de SDK"))
    s.append(body(styles, (
        "<b>Symptome :</b> VS 2026 utilisait .NET 10 SDK, mais le workload MAUI n'etait installe que sur .NET 9.<br/><br/>"
        "<b>Solution :</b> le fichier global.json force VS a utiliser le bon SDK."
    )))
    s.append(code_block(
        "// global.json place a la racine de la solution\n"
        "{\n"
        "    \"sdk\": {\n"
        "        \"version\": \"9.0.203\",\n"
        "        \"rollForward\": \"latestPatch\"\n"
        "    }\n"
        "}"
    ))
    s.append(spacer(8))

    s.append(section(styles, "12.4 Bug 4 - AccessToken vs IdToken"))
    s.append(body(styles, (
        "<b>Symptome :</b> Les utilisateurs du groupe 'finance' n'etaient pas reconnus comme managers.<br/><br/>"
        "<b>Cause :</b> on envoyait l'AccessToken a l'API, mais les claims cognito:groups ne sont pas "
        "garantis dans l'AccessToken. L'IdToken les contient toujours.<br/><br/>"
        "<b>Solution :</b> stocker et envoyer l'IdToken au lieu de l'AccessToken."
    )))
    s.append(spacer(8))
    s.append(key_box(styles, (
        "Lecon principale : les bugs viennent souvent de details subtils (un '/' manquant, un mauvais token). "
        "La methodologie : reproduire le bug, comprendre la cause racine, corriger precisement, "
        "verifier que le build passe toujours."
    )))
    s.append(PageBreak())
    return s


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 13 - GLOSSARY
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter13(styles):
    s = []
    s.append(chapter_banner("Chapitre 13 - Glossaire - Les Termes Importants"))
    s.append(spacer(10))

    terms = [
        ("AWS (Amazon Web Services)",
         "La plateforme cloud d'Amazon. Propose des centaines de services accessibles via internet."),
        ("Lambda",
         "Service AWS qui execute du code sans serveur. Le code s'execute uniquement quand declenche par un evenement."),
        ("Serverless",
         "Architecture sans serveur gere. Le cloud s'occupe de tout, on paye a l'usage."),
        ("API REST",
         "Interface de communication entre applications via HTTP. Utilise des URLs et des verbes (GET, POST, PUT, DELETE)."),
        ("HTTP",
         "Protocole de communication du web. Permet l'echange de donnees entre clients et serveurs."),
        ("JWT (JSON Web Token)",
         "Token numerique signe qui prouve l'identite et le role d'un utilisateur. Compose de 3 parties : header, payload, signature."),
        ("Bearer Token",
         "Format d'envoi du JWT dans le header HTTP : 'Authorization: Bearer <token>'."),
        ("CORS",
         "Cross-Origin Resource Sharing : mecanisme de securite qui controle quels domaines peuvent faire des requetes a un serveur."),
        ("NoSQL",
         "Type de base de donnees sans schema fixe. Exemples : DynamoDB, MongoDB."),
        ("GSI (Global Secondary Index)",
         "Index supplementaire sur une table DynamoDB qui permet de requeter selon des cles differentes de la cle principale."),
        ("PK / SK",
         "Partition Key et Sort Key - les deux parties de la cle primaire d'un item DynamoDB."),
        ("RBAC",
         "Role-Based Access Control : controle d'acces base sur les roles. Un utilisateur peut faire des actions selon son role."),
        ("SDK",
         "Software Development Kit - boite a outils pour developper avec un service specifique."),
        ("IDE",
         "Integrated Development Environment - logiciel pour coder (Visual Studio, VS Code)."),
        ("XAML",
         "Langage XML pour decrire les interfaces graphiques MAUI."),
        ("Binding",
         "Lien entre une propriete C# et un element XAML. Quand la propriete change, l'affichage se met a jour automatiquement."),
        ("Pre-signed URL",
         "URL S3 temporaire et signee qui permet un acces specifique sans authentification."),
        ("IAM",
         "Identity and Access Management - systeme de permissions AWS."),
        ("CloudWatch",
         "Service AWS de monitoring. Collecte logs, metriques, et peut declencher des alarmes."),
        ("DynamoDB",
         "Base de donnees NoSQL managee AWS. Haute performance, scalabilite automatique."),
        ("S3",
         "Simple Storage Service - stockage de fichiers AWS."),
        ("Cognito",
         "Service AWS d'authentification et de gestion des utilisateurs."),
        ("User Pool",
         "Liste d'utilisateurs Cognito avec leurs attributs et groupes."),
        ("MAUI",
         "Multi-platform App UI - framework Microsoft pour creer des apps cross-platform en C#."),
        (".NET",
         "Plateforme de developpement Microsoft. Supporte C#, F#, VB.NET."),
        ("C#",
         "Langage de programmation oriente objet de Microsoft. Fortement type, moderne."),
        ("NuGet",
         "Gestionnaire de paquets pour .NET (comme npm pour JavaScript)."),
        ("Build",
         "Compilation du code source en executable."),
        ("Deploy",
         "Deploiement de l'application sur un environnement (AWS Lambda, Windows...)."),
        ("Debug",
         "Mode de demarrage avec le debugger attache, permettant d'inspecter le code en cours d'execution."),
    ]

    # two-column glossary table
    col_w = (PAGE_W - 40*mm) / 2 - 4

    for term, definition in terms:
        row = [
            Paragraph(term, ParagraphStyle(
                "gl_term",
                fontSize=9,
                fontName="Helvetica-Bold",
                textColor=SECTION_BLUE,
                leading=13,
            )),
            Paragraph(definition, ParagraphStyle(
                "gl_def",
                fontSize=9,
                leading=13,
                textColor=DARK_GREY,
            )),
        ]
        t = Table([row], colWidths=[col_w * 0.38, col_w * 1.62])
        t.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),
        ]))
        s.append(t)

    return s


# ─────────────────────────────────────────────────────────────────────────────
# MAIN BUILD
# ─────────────────────────────────────────────────────────────────────────────
def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=20*mm,
        title="Mon Projet Expense Tracker - Guide d'apprentissage",
        author="ESTIAM Paris - Master 2 - 2026",
    )

    styles = make_styles()
    story  = []

    # Cover
    story += build_cover()

    # TOC
    story += build_toc(styles)

    # Chapters 1-13
    story += build_chapter1(styles)
    story += build_chapter2(styles)
    story += build_chapter3(styles)
    story += build_chapter4(styles)
    story += build_chapter5(styles)
    story += build_chapter6(styles)
    story += build_chapter7(styles)
    story += build_chapter8(styles)
    story += build_chapter9(styles)
    story += build_chapter10(styles)
    story += build_chapter11(styles)
    story += build_chapter12(styles)
    story += build_chapter13(styles)

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print("PDF generated successfully: " + OUTPUT_PATH)


if __name__ == "__main__":
    build_pdf()
