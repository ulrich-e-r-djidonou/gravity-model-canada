const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, LevelFormat,
        BorderStyle, WidthType, ShadingType, PageNumber, PageBreak } = require("docx");

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "Times New Roman", size: 24 }, // 12pt
        paragraph: { spacing: { line: 360 } }, // 1.5 line spacing
      },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Times New Roman" },
        paragraph: { spacing: { before: 360, after: 240 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Times New Roman" },
        paragraph: { spacing: { before: 240, after: 180 }, outlineLevel: 1 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "numbers",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          children: [new TextRun({ text: "Note m\u00e9thodologique \u2014 Mod\u00e8le gravitaire", font: "Times New Roman", size: 18, italics: true, color: "888888" })],
          alignment: AlignmentType.RIGHT,
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ children: [PageNumber.CURRENT], font: "Times New Roman", size: 20 })],
        })],
      }),
    },
    children: [
      // ── TITRE ──
      new Paragraph({ spacing: { after: 100 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: "Note m\u00e9thodologique", bold: true, size: 36, font: "Times New Roman" }),
      ]}),
      new Paragraph({ spacing: { after: 100 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: "Mod\u00e8le gravitaire des exportations canadiennes", bold: true, size: 32, font: "Times New Roman" }),
      ]}),
      new Paragraph({ spacing: { after: 200 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: "Identification des march\u00e9s sous-exploit\u00e9s pour les exportateurs canadiens", italics: true, size: 24, font: "Times New Roman" }),
      ]}),
      new Paragraph({ spacing: { after: 100 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: "[Nom]", size: 24, font: "Times New Roman" }),
      ]}),
      new Paragraph({ spacing: { after: 400 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: "Mars 2026", size: 24, font: "Times New Roman" }),
      ]}),
      new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "333333", space: 1 } }, children: [] }),
      new Paragraph({ children: [] }),

      // ── SECTION 1 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("1. Objectif")] }),
      new Paragraph({ spacing: { after: 200 }, children: [
        new TextRun("Ce projet utilise le mod\u00e8le gravitaire du commerce international pour identifier les march\u00e9s o\u00f9 le Canada exporte significativement moins que ce que les fondamentaux \u00e9conomiques et g\u00e9ographiques pr\u00e9disent. L\u2019\u00e9cart entre le flux observ\u00e9 et le flux pr\u00e9dit par le mod\u00e8le ("),
        new TextRun({ text: "trade potential gap", italics: true }),
        new TextRun(") r\u00e9v\u00e8le les opportunit\u00e9s commerciales inexploit\u00e9es \u2014 information directement pertinente pour le mandat d\u2019Exportation et d\u00e9veloppement Canada (EDC)."),
      ]}),

      // ── SECTION 2 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("2. Cadre th\u00e9orique")] }),
      new Paragraph({ spacing: { after: 200 }, children: [
        new TextRun("Le mod\u00e8le gravitaire, initialement propos\u00e9 par Tinbergen (1962) et formalis\u00e9 par Anderson et van Wincoop (2003), pr\u00e9dit que le commerce bilat\u00e9ral entre deux pays est proportionnel au produit de leurs PIB et inversement proportionnel \u00e0 la distance qui les s\u00e9pare, ajust\u00e9 pour les co\u00fbts commerciaux (barri\u00e8res tarifaires, langue, fronti\u00e8re commune, accords commerciaux)."),
      ]}),
      new Paragraph({ spacing: { after: 100 }, children: [
        new TextRun("L\u2019\u00e9quation structurelle du mod\u00e8le prend la forme\u00a0:"),
      ]}),
      new Paragraph({ spacing: { after: 100 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: "X", italics: true }),
        new TextRun({ text: "ij", italics: true, subScript: true }),
        new TextRun(" = ("),
        new TextRun({ text: "Y", italics: true }),
        new TextRun({ text: "i", italics: true, subScript: true }),
        new TextRun(" \u00d7 "),
        new TextRun({ text: "Y", italics: true }),
        new TextRun({ text: "j", italics: true, subScript: true }),
        new TextRun(") / ("),
        new TextRun({ text: "d", italics: true }),
        new TextRun({ text: "ij", italics: true, subScript: true }),
        new TextRun({ text: "\u03b8", superScript: true }),
        new TextRun(" \u00d7 "),
        new TextRun({ text: "R", italics: true }),
        new TextRun({ text: "i", italics: true, subScript: true }),
        new TextRun(" \u00d7 "),
        new TextRun({ text: "R", italics: true }),
        new TextRun({ text: "j", italics: true, subScript: true }),
        new TextRun(")"),
      ]}),
      new Paragraph({ spacing: { after: 200 }, children: [
        new TextRun("o\u00f9 "),
        new TextRun({ text: "X", italics: true }),
        new TextRun({ text: "ij", italics: true, subScript: true }),
        new TextRun(" repr\u00e9sente les exportations du pays "),
        new TextRun({ text: "i", italics: true }),
        new TextRun(" vers le pays "),
        new TextRun({ text: "j", italics: true }),
        new TextRun(", "),
        new TextRun({ text: "Y", italics: true }),
        new TextRun(" les PIB respectifs, "),
        new TextRun({ text: "d", italics: true }),
        new TextRun(" la distance bilat\u00e9rale, "),
        new TextRun({ text: "\u03b8", italics: true }),
        new TextRun(" l\u2019\u00e9lasticit\u00e9 de la distance, et "),
        new TextRun({ text: "R", italics: true }),
        new TextRun(" les termes de r\u00e9sistance multilat\u00e9rale."),
      ]}),

      // ── SECTION 3 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("3. Estimateur \u2014 PPML")] }),
      new Paragraph({ spacing: { after: 200 }, children: [
        new TextRun("Nous utilisons l\u2019estimateur Poisson Pseudo-Maximum Likelihood (PPML) de Santos Silva et Tenreyro (2006). Cet estimateur pr\u00e9sente deux avantages majeurs par rapport \u00e0 l\u2019OLS traditionnellement utilis\u00e9\u00a0:"),
      ]}),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 100 }, children: [
        new TextRun({ text: "Inclusion des flux z\u00e9ro\u00a0: ", bold: true }),
        new TextRun("L\u2019OLS en log-lin\u00e9aire exclut les paires de pays sans commerce bilat\u00e9ral, introduisant un biais de s\u00e9lection. Le PPML estime la variable d\u00e9pendante en niveaux et inclut les z\u00e9ros."),
      ]}),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 200 }, children: [
        new TextRun({ text: "Correction de l\u2019h\u00e9t\u00e9rosc\u00e9dasticit\u00e9\u00a0: ", bold: true }),
        new TextRun("Santos Silva et Tenreyro (2006) d\u00e9montrent que l\u2019OLS log-lin\u00e9aire produit des estimateurs inconsistants en pr\u00e9sence d\u2019h\u00e9t\u00e9rosc\u00e9dasticit\u00e9, probl\u00e8me courant dans les donn\u00e9es de commerce. Le PPML est robuste \u00e0 ce probl\u00e8me."),
      ]}),

      // ── SECTION 4 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("4. Donn\u00e9es")] }),
      new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "Sources\u00a0:", bold: true })] }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [
        new TextRun("USITC Dynamic Gravity Dataset v2.1 (2000\u20132019)\u00a0: variables gravitaires bilat\u00e9rales"),
      ]}),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [
        new TextRun("UN Comtrade API v2\u00a0: flux commerciaux bilat\u00e9raux du Canada (exportations FOB)"),
      ]}),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 200 }, children: [
        new TextRun("Banque mondiale WDI\u00a0: PIB et population"),
      ]}),
      new Paragraph({ spacing: { after: 100 }, children: [
        new TextRun({ text: "Panel\u00a0: ", bold: true }),
        new TextRun("4\u00a0993 observations, 254 pays partenaires, 20 ann\u00e9es (2000\u20132019)."),
      ]}),

      // Variables table
      new Paragraph({ spacing: { before: 200, after: 100 }, children: [new TextRun({ text: "Variables\u00a0:", bold: true })] }),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [4000, 5360],
        rows: [
          ["Variable", "Description"],
          ["Exportations (Y)", "Exportations du Canada vers le pays j (USD)"],
          ["Distance", "Distance bilat\u00e9rale (km, population-weighted)"],
          ["Contigu\u00eft\u00e9", "Fronti\u00e8re commune (dummy)"],
          ["Langue commune", "Langue officielle commune (dummy)"],
          ["Colonie", "Pass\u00e9 colonial commun (dummy)"],
          ["ALE/RTA", "Accord de libre-\u00e9change (dummy)"],
          ["PIB partenaire", "PIB du partenaire (USD courant)"],
          ["Population", "Population du partenaire"],
        ].map((row, i) => new TableRow({
          children: row.map((cell, j) => new TableCell({
            borders,
            width: { size: j === 0 ? 4000 : 5360, type: WidthType.DXA },
            shading: i === 0 ? { fill: "D5E8F0", type: ShadingType.CLEAR } : undefined,
            margins: { top: 60, bottom: 60, left: 100, right: 100 },
            children: [new Paragraph({ children: [new TextRun({ text: cell, bold: i === 0, size: 22 })] })],
          })),
        })),
      }),

      // ── SECTION 5 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("5. Sp\u00e9cifications")] }),
      new Paragraph({ spacing: { after: 100 }, children: [new TextRun("Trois sp\u00e9cifications sont estim\u00e9es\u00a0:")] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 100 }, children: [
        new TextRun({ text: "OLS baseline\u00a0: ", bold: true }),
        new TextRun("ln(trade) = \u03b1 + \u03b2\u00b7ln(dist) + \u03b3\u00b7Z + \u03b5 (exclut les z\u00e9ros, sert de benchmark)"),
      ]}),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 100 }, children: [
        new TextRun({ text: "PPML\u00a0: ", bold: true }),
        new TextRun("trade = exp(\u03b1 + \u03b2\u00b7ln(dist) + \u03b3\u00b7Z) \u00d7 \u03b5 (corrige le biais de s\u00e9lection et l\u2019h\u00e9t\u00e9rosc\u00e9dasticit\u00e9)"),
      ]}),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 200 }, children: [
        new TextRun({ text: "PPML avec effets fixes\u00a0: ", bold: true }),
        new TextRun("trade = exp(\u03b1 + \u03b2\u00b7ln(dist) + \u03b3\u00b7Z + \u03bc"),
        new TextRun({ text: "t", subScript: true }),
        new TextRun(") \u00d7 \u03b5 (contr\u00f4le les tendances globales)"),
      ]}),

      // ── SECTION 6 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("6. Calcul du potentiel commercial")] }),
      new Paragraph({ spacing: { after: 100 }, children: [
        new TextRun("Le potentiel commercial est d\u00e9fini comme le ratio entre le flux pr\u00e9dit par le mod\u00e8le et le flux observ\u00e9\u00a0:"),
      ]}),
      new Paragraph({ spacing: { after: 200 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: "Potential", italics: true }),
        new TextRun({ text: "j", italics: true, subScript: true }),
        new TextRun(" = "),
        new TextRun({ text: "Trade", italics: true }),
        new TextRun({ text: "pr\u00e9dit,j", italics: true, subScript: true }),
        new TextRun(" / "),
        new TextRun({ text: "Trade", italics: true }),
        new TextRun({ text: "r\u00e9el,j", italics: true, subScript: true }),
      ]}),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [3120, 3120, 3120],
        rows: [
          ["Classification", "Crit\u00e8re", "Interpr\u00e9tation"],
          ["Sous-exploit\u00e9", "Ratio > 1,25", "Opportunit\u00e9 commerciale"],
          ["\u00c9quilibre", "0,75 < Ratio < 1,25", "Commerce conforme aux fondamentaux"],
          ["Sur-exploit\u00e9", "Ratio < 0,75", "D\u00e9pendance commerciale"],
        ].map((row, i) => new TableRow({
          children: row.map(cell => new TableCell({
            borders,
            width: { size: 3120, type: WidthType.DXA },
            shading: i === 0 ? { fill: "D5E8F0", type: ShadingType.CLEAR } : undefined,
            margins: { top: 60, bottom: 60, left: 100, right: 100 },
            children: [new Paragraph({ children: [new TextRun({ text: cell, bold: i === 0, size: 22 })] })],
          })),
        })),
      }),

      // ── SECTION 7 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("7. Sc\u00e9narios contrefactuels")] }),
      new Paragraph({ spacing: { after: 100 }, children: [
        new TextRun("Le mod\u00e8le permet de simuler l\u2019impact de changements de politique commerciale\u00a0:"),
      ]}),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [
        new TextRun({ text: "Nouvel ALE\u00a0: ", bold: true }),
        new TextRun("passage de la variable RTA de 0 \u00e0 1 pour les pays cibl\u00e9s"),
      ]}),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [
        new TextRun({ text: "Sanctions\u00a0: ", bold: true }),
        new TextRun("choc n\u00e9gatif sur le PIB effectif du partenaire et retrait de l\u2019ALE"),
      ]}),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 200 }, children: [
        new TextRun({ text: "Choc macro\u00e9conomique\u00a0: ", bold: true }),
        new TextRun("variation du PIB du partenaire"),
      ]}),
      new Paragraph({ spacing: { after: 200 }, children: [
        new TextRun("Ces simulations sont partielles ("),
        new TextRun({ text: "partial equilibrium", italics: true }),
        new TextRun(") et ne tiennent pas compte des effets d\u2019\u00e9quilibre g\u00e9n\u00e9ral, de la diversion commerciale, ni des ajustements de prix. Elles fournissent une approximation de premier ordre de l\u2019impact potentiel."),
      ]}),

      // ── SECTION 8 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("8. Limites")] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 }, children: [
        new TextRun("Le mod\u00e8le est unilat\u00e9ral (Canada comme seul exportateur), ce qui ne contr\u00f4le pas les r\u00e9sistances multilat\u00e9rales c\u00f4t\u00e9 exportateur."),
      ]}),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 }, children: [
        new TextRun("Les donn\u00e9es Comtrade sont limit\u00e9es \u00e0 2019 (pr\u00e9-COVID, pr\u00e9-sanctions Russie)."),
      ]}),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 }, children: [
        new TextRun("Le PPML sans effets fixes importateur ne contr\u00f4le pas parfaitement les caract\u00e9ristiques inobserv\u00e9es des partenaires."),
      ]}),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 200 }, children: [
        new TextRun("Les sc\u00e9narios contrefactuels sont en \u00e9quilibre partiel."),
      ]}),

      // ── SECTION 9 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("9. R\u00e9f\u00e9rences")] }),
      new Paragraph({ spacing: { after: 100 }, indent: { left: 720, hanging: 720 }, children: [
        new TextRun("Anderson, J.E. et van Wincoop, E. (2003). Gravity with Gravitas: A Solution to the Border Puzzle. "),
        new TextRun({ text: "American Economic Review", italics: true }),
        new TextRun(", 93(1), 170\u2013192."),
      ]}),
      new Paragraph({ spacing: { after: 100 }, indent: { left: 720, hanging: 720 }, children: [
        new TextRun("Santos Silva, J.M.C. et Tenreyro, S. (2006). The Log of Gravity. "),
        new TextRun({ text: "Review of Economics and Statistics", italics: true }),
        new TextRun(", 88(4), 641\u2013658."),
      ]}),
      new Paragraph({ spacing: { after: 100 }, indent: { left: 720, hanging: 720 }, children: [
        new TextRun("Tinbergen, J. (1962). "),
        new TextRun({ text: "Shaping the World Economy: Suggestions for an International Economic Policy", italics: true }),
        new TextRun(". New York: Twentieth Century Fund."),
      ]}),
      new Paragraph({ spacing: { after: 100 }, indent: { left: 720, hanging: 720 }, children: [
        new TextRun("Yotov, Y.V., Piermartini, R., Monteiro, J.-A. et Larch, M. (2016). "),
        new TextRun({ text: "An Advanced Guide to Trade Policy Analysis: The Structural Gravity Model", italics: true }),
        new TextRun(". WTO/UNCTAD."),
      ]}),
    ],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("C:/Users/ulric/Downloads/EDC_model/gravity_model_canada/docs/note_methodologique.docx", buffer);
  console.log("Document created successfully");
});
