#!/usr/bin/env node
/**
 * print-pdf.cjs — Puppeteer PDF renderer
 * 
 * v2: displayHeaderFooter is ALWAYS disabled.
 * Header/footer stamping is handled by PyMuPDF post-processing in build-pdf.py.
 * This gives full control over per-page visibility (even/odd, skip image pages).
 */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

async function main() {
  const htmlPath = process.argv[2];
  const pdfPath = process.argv[3];
  const opts = JSON.parse(process.argv[4] || '{}');

  const browser = await puppeteer.launch({
    executablePath: opts.chrome || '/home/takahara/.cache/vivliostyle/browsers/chrome/linux-149.0.7827.22/chrome-linux64/chrome',
    args: ['--no-sandbox', '--disable-gpu', '--headless=new', '--allow-file-access-from-files'],
  });

  try {
    const page = await browser.newPage();
    
    // Log console messages for debugging
    page.on('console', msg => console.log('PAGE LOG:', msg.type(), msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
    
    const fileUrl = 'file://' + path.resolve(htmlPath);
    await page.goto(fileUrl, { waitUntil: 'load', timeout: 120000 });
    
    // Small delay to ensure images are fully decoded
    await new Promise(r => setTimeout(r, 2000));

    const pdfOpts = {
      format: 'A6',
      landscape: false,
      displayHeaderFooter: false,  // ALWAYS false — PyMuPDF handles stamping
      margin: opts.margin || { top: '0', bottom: '0', left: '0', right: '0' },
      printBackground: true,
      preferCSSPageSize: true,
    };

    const pdf = await page.pdf(pdfOpts);
    fs.writeFileSync(pdfPath, pdf);
    console.log('OK ' + pdf.length);
  } finally {
    await browser.close();
  }
}

main().catch(e => { console.error('ERROR ' + e.message); process.exit(1); });
