const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, ExternalHyperlink,
        AlignmentType, LevelFormat, BorderStyle } = require("docx");

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "Arial", size: 22 }, // 11pt
        paragraph: { spacing: { line: 276 } }, // 1.15 line spacing
      },
    },
  },
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } },
      }],
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    children: [
      // Header info
      new Paragraph({ spacing: { after: 40 }, children: [
        new TextRun({ text: "[Nom]", bold: true, size: 24 }),
      ]}),
      new Paragraph({ spacing: { after: 40 }, children: [
        new TextRun({ text: "[Adresse]", color: "555555" }),
      ]}),
      new Paragraph({ spacing: { after: 300 }, children: [
        new TextRun({ text: "[Courriel] | [T\u00e9l\u00e9phone]", color: "555555" }),
      ]}),

      // Date
      new Paragraph({ spacing: { after: 300 }, children: [
        new TextRun("Le 21 mars 2026"),
      ]}),

      // Recipient
      new Paragraph({ spacing: { after: 40 }, children: [
        new TextRun({ text: "Export Development Canada", bold: true }),
      ]}),
      new Paragraph({ spacing: { after: 40 }, children: [
        new TextRun("Poste : Quantitative Analyst-Economist (R\u00e9f. 0005NX)"),
      ]}),
      new Paragraph({ spacing: { after: 300 }, children: [
        new TextRun("\u00c9quipe DREAM \u2014 Economic and Political Intelligence Centre"),
      ]}),

      // Subject
      new Paragraph({ spacing: { after: 300 }, children: [
        new TextRun({ text: "Objet : Candidature au poste de Quantitative Analyst-Economist", bold: true }),
      ]}),

      // Salutation
      new Paragraph({ spacing: { after: 200 }, children: [
        new TextRun("Madame, Monsieur,"),
      ]}),

      // Intro paragraph
      new Paragraph({ spacing: { after: 200 }, children: [
        new TextRun("Je vous \u00e9cris pour exprimer mon int\u00e9r\u00eat pour le poste de Quantitative Analyst-Economist au sein de l\u2019\u00e9quipe DREAM d\u2019EDC. \u00c9conomiste avec plus de six ans d\u2019exp\u00e9rience en mod\u00e9lisation quantitative, analyse de donn\u00e9es macro\u00e9conomiques et inf\u00e9rence causale, je suis convaincu que mon profil correspond \u00e9troitement aux exigences de ce r\u00f4le."),
      ]}),

      // Section 1
      new Paragraph({ spacing: { before: 200, after: 120 }, children: [
        new TextRun({ text: "MOD\u00c9LISATION \u00c9CONOM\u00c9TRIQUE ET PR\u00c9VISION MACRO\u00c9CONOMIQUE", bold: true, size: 22 }),
      ]}),
      new Paragraph({ spacing: { after: 120 }, children: [
        new TextRun("Mon exp\u00e9rience en \u00e9conom\u00e9trie appliqu\u00e9e couvre les mod\u00e8les de panel, les s\u00e9ries temporelles et les m\u00e9thodes d\u2019estimation avanc\u00e9es (PPML, GMM, effets fixes haute dimension). Pour illustrer ma capacit\u00e9 \u00e0 d\u00e9velopper des mod\u00e8les de risque souverain et d\u2019analyse commerciale, j\u2019ai construit un mod\u00e8le gravitaire des exportations canadiennes ("),
        new ExternalHyperlink({
          children: [new TextRun({ text: "github.com/ulrich-e-r-djidonou/gravity-model-canada", style: "Hyperlink" })],
          link: "https://github.com/ulrich-e-r-djidonou/gravity-model-canada",
        }),
        new TextRun(") qui :"),
      ]}),

      // Bullet points
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [
        new TextRun("Estime les flux commerciaux bilat\u00e9raux du Canada avec 254 partenaires (2000\u20132019) via PPML avec effets fixes, l\u2019estimateur de r\u00e9f\u00e9rence en commerce international"),
      ]}),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [
        new TextRun("Identifie $24.4 milliards de potentiel commercial inexploit\u00e9 sur 116 march\u00e9s"),
      ]}),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [
        new TextRun("Simule des sc\u00e9narios contrefactuels (impact d\u2019un ALE avec l\u2019ASEAN : +$3.1B ; sanctions Russie : \u2013$1.2B)"),
      ]}),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 120 }, children: [
        new TextRun("D\u00e9compose le potentiel par secteur (manufacturier, \u00e9nergie, agriculture) et par march\u00e9 \u00e9mergent"),
      ]}),

      new Paragraph({ spacing: { after: 200 }, children: [
        new TextRun("Ce projet d\u00e9montre exactement le type d\u2019analyse que l\u2019\u00e9quipe DREAM r\u00e9alise : mod\u00e9lisation de risque, pr\u00e9vision par march\u00e9, et production de dashboards d\u2019aide \u00e0 la d\u00e9cision."),
      ]}),

      // Section 2
      new Paragraph({ spacing: { before: 200, after: 120 }, children: [
        new TextRun({ text: "COMP\u00c9TENCES TECHNIQUES", bold: true, size: 22 }),
      ]}),
      new Paragraph({ spacing: { after: 200 }, children: [
        new TextRun("Python est mon outil principal de travail. Je ma\u00eetrise l\u2019\u00e9cosyst\u00e8me de data science (pandas, statsmodels, scikit-learn, pyfixest) ainsi que la visualisation interactive (Plotly, Streamlit, Power BI). Mon exp\u00e9rience avec les bases de donn\u00e9es macro\u00e9conomiques (FMI, Banque mondiale, Comtrade, CEPII) et les API de donn\u00e9es me permet de travailler efficacement avec les grandes bases que maintient l\u2019\u00e9quipe DREAM."),
      ]}),

      // Section 3
      new Paragraph({ spacing: { before: 200, after: 120 }, children: [
        new TextRun({ text: "DOCUMENTATION ET RIGUEUR R\u00c9GLEMENTAIRE", bold: true, size: 22 }),
      ]}),
      new Paragraph({ spacing: { after: 200 }, children: [
        new TextRun("Je comprends l\u2019importance de la documentation m\u00e9thodologique dans un contexte r\u00e9glementaire (IFRS9, B\u00e2le). Mon travail acad\u00e9mique et professionnel m\u2019a form\u00e9 \u00e0 produire des notes m\u00e9thodologiques rigoureuses, des rapports de validation et de la documentation de mod\u00e8les conforme aux standards d\u2019audit."),
      ]}),

      // Section 4
      new Paragraph({ spacing: { before: 200, after: 120 }, children: [
        new TextRun({ text: "BILINGUISME ET COLLABORATION", bold: true, size: 22 }),
      ]}),
      new Paragraph({ spacing: { after: 200 }, children: [
        new TextRun("Parfaitement bilingue (fran\u00e7ais et anglais), je suis \u00e0 l\u2019aise dans des environnements multidisciplinaires o\u00f9 la communication claire entre \u00e9conomistes, actuaires et d\u00e9cideurs est essentielle."),
      ]}),

      // Closing
      new Paragraph({ spacing: { after: 200 }, children: [
        new TextRun("Je serais ravi de discuter de la mani\u00e8re dont mon exp\u00e9rience peut contribuer aux mandats de l\u2019\u00e9quipe DREAM. Je vous remercie de l\u2019attention port\u00e9e \u00e0 ma candidature."),
      ]}),

      // Signature
      new Paragraph({ spacing: { after: 40 }, children: [
        new TextRun("Cordialement,"),
      ]}),
      new Paragraph({ spacing: { before: 300, after: 300 }, children: [
        new TextRun({ text: "[Nom]", bold: true }),
      ]}),

      // Separator
      new Paragraph({
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC", space: 1 } },
        spacing: { after: 120 },
        children: [],
      }),

      // Attachments
      new Paragraph({ spacing: { after: 40 }, children: [
        new TextRun({ text: "Pi\u00e8ces jointes :", bold: true, size: 20, color: "555555" }),
      ]}),
      new Paragraph({ spacing: { after: 20 }, children: [
        new TextRun({ text: "- Curriculum vitae", size: 20, color: "555555" }),
      ]}),
      new Paragraph({ children: [
        new TextRun({ text: "- Portfolio : ", size: 20, color: "555555" }),
        new ExternalHyperlink({
          children: [new TextRun({ text: "github.com/ulrich-e-r-djidonou/gravity-model-canada", style: "Hyperlink", size: 20 })],
          link: "https://github.com/ulrich-e-r-djidonou/gravity-model-canada",
        }),
      ]}),
    ],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("C:/Users/ulric/Downloads/EDC_model/gravity_model_canada/docs/cover_letter_EDC.docx", buffer);
  console.log("Cover letter created successfully");
});
