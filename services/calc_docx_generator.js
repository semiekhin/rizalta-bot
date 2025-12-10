const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
        AlignmentType, BorderStyle, WidthType, ShadingType } = require('docx');
const fs = require('fs');

const COLORS = { green: "313D20", gold: "DCB764", ivory: "F6F0E3", black: "000000", gray: "666666" };

function createROIDocument(data) {
    const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
    const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };
    
    // Header row for years table
    const headerRow = new TableRow({ children: [
        new TableCell({ borders: cellBorders, shading: { fill: COLORS.green, type: ShadingType.CLEAR },
            children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Год", bold: true, color: "FFFFFF" })] })] }),
        new TableCell({ borders: cellBorders, shading: { fill: COLORS.green, type: ShadingType.CLEAR },
            children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Аренда", bold: true, color: "FFFFFF" })] })] }),
        new TableCell({ borders: cellBorders, shading: { fill: COLORS.green, type: ShadingType.CLEAR },
            children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Рост стоим.", bold: true, color: "FFFFFF" })] })] }),
        new TableCell({ borders: cellBorders, shading: { fill: COLORS.green, type: ShadingType.CLEAR },
            children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Доход %", bold: true, color: "FFFFFF" })] })] })
    ]});
    
    // Data rows
    const yearRows = [headerRow];
    data.years.forEach(function(y) {
        yearRows.push(new TableRow({ children: [
            new TableCell({ borders: cellBorders, width: { size: 1800, type: WidthType.DXA },
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun(y.year)] })] }),
            new TableCell({ borders: cellBorders, width: { size: 2400, type: WidthType.DXA },
                children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun(y.rental)] })] }),
            new TableCell({ borders: cellBorders, width: { size: 2400, type: WidthType.DXA },
                children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun(y.growth)] })] }),
            new TableCell({ borders: cellBorders, width: { size: 1800, type: WidthType.DXA },
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: y.total_pct, bold: true, color: COLORS.green })] })] })
        ]}));
    });

    const doc = new Document({
        sections: [{
            properties: { page: { margin: { top: 800, right: 800, bottom: 800, left: 800 } } },
            children: [
                new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
                    children: [new TextRun({ text: "RIZALTA RESORT BELOKURIKHA", bold: true, size: 28, color: COLORS.green })] }),
                new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 },
                    children: [new TextRun({ text: "Инвестиционный расчёт: " + data.title, bold: true, size: 36, color: COLORS.black })] }),
                
                new Paragraph({ spacing: { before: 200 }, children: [new TextRun({ text: "Параметры", bold: true, size: 26, color: COLORS.green })] }),
                new Table({ columnWidths: [4000, 4000], rows: [
                    new TableRow({ children: [
                        new TableCell({ borders: cellBorders, shading: { fill: COLORS.ivory, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Площадь", bold: true })] })] }),
                        new TableCell({ borders: cellBorders, children: [new Paragraph({ children: [new TextRun(data.area || "")] })] })
                    ]}),
                    new TableRow({ children: [
                        new TableCell({ borders: cellBorders, shading: { fill: COLORS.ivory, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Цена за м²", bold: true })] })] }),
                        new TableCell({ borders: cellBorders, children: [new Paragraph({ children: [new TextRun(data.price_m2 || "")] })] })
                    ]}),
                    new TableRow({ children: [
                        new TableCell({ borders: cellBorders, shading: { fill: COLORS.ivory, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Стоимость", bold: true })] })] }),
                        new TableCell({ borders: cellBorders, children: [new Paragraph({ children: [new TextRun(data.price || "")] })] })
                    ]})
                ]}),
                
                new Paragraph({ spacing: { before: 300 }, children: [new TextRun({ text: "Прогноз прибыли по годам", bold: true, size: 26, color: COLORS.green })] }),
                new Table({ columnWidths: [1800, 2400, 2400, 1800], rows: yearRows }),
                
                new Paragraph({ spacing: { before: 300 }, children: [new TextRun({ text: "Итого за 11 лет (2025-2035)", bold: true, size: 26, color: COLORS.green })] }),
                new Table({ columnWidths: [4000, 4000], rows: [
                    new TableRow({ children: [
                        new TableCell({ borders: cellBorders, shading: { fill: COLORS.ivory, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Прибыль от аренды", bold: true })] })] }),
                        new TableCell({ borders: cellBorders, children: [new Paragraph({ children: [new TextRun(data.total_rental || "")] })] })
                    ]}),
                    new TableRow({ children: [
                        new TableCell({ borders: cellBorders, shading: { fill: COLORS.ivory, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Прибыль от роста", bold: true })] })] }),
                        new TableCell({ borders: cellBorders, children: [new Paragraph({ children: [new TextRun(data.total_growth || "")] })] })
                    ]}),
                    new TableRow({ children: [
                        new TableCell({ borders: cellBorders, shading: { fill: COLORS.gold, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "ОБЩАЯ ПРИБЫЛЬ", bold: true })] })] }),
                        new TableCell({ borders: cellBorders, shading: { fill: COLORS.gold, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: data.total_profit || "", bold: true })] })] })
                    ]}),
                    new TableRow({ children: [
                        new TableCell({ borders: cellBorders, shading: { fill: COLORS.ivory, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Доходность за 11 лет", bold: true })] })] }),
                        new TableCell({ borders: cellBorders, children: [new Paragraph({ children: [new TextRun({ text: data.roi_pct || "", bold: true, color: COLORS.green })] })] })
                    ]}),
                    new TableRow({ children: [
                        new TableCell({ borders: cellBorders, shading: { fill: COLORS.ivory, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Средняя годовая", bold: true })] })] }),
                        new TableCell({ borders: cellBorders, children: [new Paragraph({ children: [new TextRun({ text: data.avg_annual_pct || "", bold: true, color: COLORS.green })] })] })
                    ]}),
                    new TableRow({ children: [
                        new TableCell({ borders: cellBorders, shading: { fill: COLORS.ivory, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Стоимость в 2035", bold: true })] })] }),
                        new TableCell({ borders: cellBorders, children: [new Paragraph({ children: [new TextRun(data.final_value || "")] })] })
                    ]})
                ]}),
                
                new Paragraph({ spacing: { before: 400 }, alignment: AlignmentType.CENTER,
                    children: [new TextRun({ text: "RIZALTA RESORT BELOKURIKHA", size: 18, color: COLORS.gray })] })
            ]
        }]
    });
    return doc;
}

var args = process.argv.slice(2);
var data = JSON.parse(args[0]);
var outputPath = args[1];

var doc = createROIDocument(data);
Packer.toBuffer(doc).then(function(buffer) {
    fs.writeFileSync(outputPath, buffer);
    console.log("[DOCX] Created: " + outputPath);
});
