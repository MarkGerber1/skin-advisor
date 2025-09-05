#!/usr/bin/env node

/**
 * SVG to PNG Converter for Beauty Care Bot Brand Assets
 * Converts SVG files to PNG format (512x512px)
 */

const fs = require('fs');
const path = require('path');
const { createCanvas, loadImage } = require('canvas');

// Files to convert
const files = [
    { input: 'ui/brand/logo.svg', output: 'ui/brand/logo.png' },
    { input: 'ui/brand/logo-dark.svg', output: 'ui/brand/logo-dark.png' },
    { input: 'ui/brand/stickers/palette.svg', output: 'ui/brand/stickers/palette.png' },
    { input: 'ui/brand/stickers/heart-lipstick.svg', output: 'ui/brand/stickers/heart-lipstick.png' },
    { input: 'ui/brand/stickers/drop.svg', output: 'ui/brand/stickers/drop.png' }
];

async function convertSVGtoPNG(inputPath, outputPath) {
    try {
        console.log(`🔄 Converting ${inputPath} to ${outputPath}...`);

        // Read SVG content
        const svgContent = fs.readFileSync(inputPath, 'utf8');

        // Create canvas
        const canvas = createCanvas(512, 512);
        const ctx = canvas.getContext('2d');

        // Fill with white background (for PNG transparency issues)
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, 512, 512);

        // For SVG rendering, we'll create a data URL
        const dataUrl = `data:image/svg+xml;base64,${Buffer.from(svgContent).toString('base64')}`;

        // Load and draw SVG
        const img = await loadImage(dataUrl);
        ctx.drawImage(img, 0, 0, 512, 512);

        // Save as PNG
        const buffer = canvas.toBuffer('image/png');
        fs.writeFileSync(outputPath, buffer);

        console.log(`✅ Converted ${outputPath}`);
        return true;
    } catch (error) {
        console.error(`❌ Error converting ${inputPath}:`, error.message);
        return false;
    }
}

async function main() {
    console.log('🎨 Beauty Care Bot - SVG to PNG Converter');
    console.log('==========================================\n');

    let successCount = 0;
    let totalCount = files.length;

    for (const file of files) {
        // Ensure output directory exists
        const outputDir = path.dirname(file.output);
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        // Check if input file exists
        if (!fs.existsSync(file.input)) {
            console.log(`⚠️  Input file not found: ${file.input}`);
            continue;
        }

        // Convert file
        const success = await convertSVGtoPNG(file.input, file.output);
        if (success) {
            successCount++;
        }
    }

    console.log('\n==========================================');
    console.log(`📊 Conversion complete: ${successCount}/${totalCount} files converted`);

    if (successCount === totalCount) {
        console.log('🎉 All brand assets converted successfully!');
        console.log('\n📁 Generated files:');
        files.forEach(file => {
            console.log(`   • ${file.output}`);
        });
    } else {
        console.log('⚠️  Some files could not be converted. Check the errors above.');
        process.exit(1);
    }
}

// Check if canvas is available
try {
    require('canvas');
} catch (error) {
    console.error('❌ Canvas module not found. Install it with: npm install canvas');
    console.log('\nAlternative: Use the HTML converter at ui/brand/convert-svg-to-png.html');
    process.exit(1);
}

// Run converter
main().catch(error => {
    console.error('❌ Unexpected error:', error);
    process.exit(1);
});



