import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

function stripEmoji(str) {
  return (str || '').replace(/[\p{Emoji_Presentation}\p{Extended_Pictographic}]/gu, '').trim()
}

function fmt(eur) {
  return eur > 0 ? `${eur.toFixed(2)} EUR` : '-'
}

export function generateTallyPDF(allSummaries, drinks) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })

  const now = new Date()
  const dateStr = now.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
  const timeStr = now.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })

  const GREEN  = [44, 95, 46]
  const LGRAY  = [245, 245, 245]
  const MGRAY  = [200, 200, 200]
  const BLACK  = [26, 26, 26]
  const WHITE  = [255, 255, 255]
  const SUBTOT = [232, 245, 233]

  const activeSummaries = allSummaries.filter(s => s.grand_total > 0)

  // ── Header-Banner ────────────────────────────────────────────
  doc.setFillColor(...GREEN)
  doc.rect(0, 0, 210, 28, 'F')

  doc.setTextColor(...WHITE)
  doc.setFontSize(20)
  doc.setFont('helvetica', 'bold')
  doc.text('Getranke-Abrechnung', 14, 13)

  doc.setFontSize(10)
  doc.setFont('helvetica', 'normal')
  doc.text('Bauwagen DB', 14, 21)
  doc.text(`Erstellt am ${dateStr} um ${timeStr} Uhr`, 210 - 14, 21, { align: 'right' })
  doc.setTextColor(...BLACK)

  // ── Spalten ──────────────────────────────────────────────────
  const columns = ['Name', 'Getrank', 'Anzahl', 'GL-Preis', 'Gesamt']

  // ── Zeilen aufbauen ──────────────────────────────────────────
  const rows = []
  let grandAmount = 0
  let grandCost = 0

  for (const summary of activeSummaries) {
    let glFirst = true
    let glAmount = 0
    let glCost = 0

    for (const entry of summary.entries) {
      if (entry.total <= 0) continue

      const drink = drinks.find(d => d.id === entry.drink_id)
      const glPrice = (drink?.price_gl != null) ? drink.price_gl : null
      const lineCost = (glPrice != null) ? glPrice * entry.total : 0

      glAmount += entry.total
      glCost += lineCost

      rows.push({
        data: [
          glFirst ? summary.display_name : '',
          stripEmoji(entry.drink_name),
          String(entry.total),
          glPrice != null ? `${glPrice.toFixed(2)} EUR` : 'gratis',
          glPrice != null && glPrice > 0 ? `${lineCost.toFixed(2)} EUR` : '-',
        ],
        isSubtotal: false,
        isGrandTotal: false,
      })
      glFirst = false
    }

    // Zwischensumme pro GL
    rows.push({
      data: [
        `Gesamt ${summary.display_name}`,
        '',
        String(glAmount),
        '',
        fmt(glCost),
      ],
      isSubtotal: true,
      isGrandTotal: false,
    })

    grandAmount += glAmount
    grandCost += glCost
  }

  // Grand Total
  rows.push({
    data: ['TOTAL', '', String(grandAmount), '', fmt(grandCost)],
    isSubtotal: false,
    isGrandTotal: true,
  })

  // ── Tabelle ──────────────────────────────────────────────────
  autoTable(doc, {
    startY: 34,
    head: [columns],
    body: rows.map(r => r.data),
    theme: 'grid',
    styles: {
      font: 'helvetica',
      fontSize: 11,
      cellPadding: { top: 4, bottom: 4, left: 5, right: 5 },
      textColor: BLACK,
      lineColor: MGRAY,
    },
    headStyles: {
      fillColor: GREEN,
      textColor: WHITE,
      fontStyle: 'bold',
    },
    columnStyles: {
      2: { halign: 'center' },
      3: { halign: 'right' },
      4: { halign: 'right' },
    },
    alternateRowStyles: { fillColor: LGRAY },
    didParseCell(data) {
      const rowMeta = rows[data.row.index]
      if (!rowMeta) return
      if (rowMeta.isGrandTotal) {
        data.cell.styles.fillColor = GREEN
        data.cell.styles.textColor = WHITE
        data.cell.styles.fontStyle = 'bold'
        data.cell.styles.fontSize = 12
      } else if (rowMeta.isSubtotal) {
        data.cell.styles.fillColor = SUBTOT
        data.cell.styles.fontStyle = 'bold'
        data.cell.styles.textColor = GREEN
      }
    },
  })

  // ── Footer ───────────────────────────────────────────────────
  const pageCount = doc.getNumberOfPages()
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i)
    doc.setFontSize(9)
    doc.setTextColor(150)
    doc.text(`Seite ${i} von ${pageCount}`, 210 - 14, 297 - 8, { align: 'right' })
    doc.text('Bauwagen DB', 14, 297 - 8)
  }

  const filename = `Strichliste_${dateStr.replace(/\./g, '-')}_${timeStr.replace(':', '')}.pdf`
  doc.save(filename)
}
