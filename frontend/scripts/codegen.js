import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { compileFromFile } from 'json-schema-to-typescript';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT_SCHEMAS_DIR = path.resolve(__dirname, '../../schemas');
const TARGET_TYPES_DIR = path.resolve(__dirname, '../src/types/generated');

async function generateTypes() {
  console.log('🔄 Generating TypeScript types from JSON Schemas...');

  const schemaDirs = ['api', 'mqtt'];
  const allExports = [];

  for (const dir of schemaDirs) {
    const srcDir = path.join(ROOT_SCHEMAS_DIR, dir);
    const destDir = path.join(TARGET_TYPES_DIR, dir);

    if (!fs.existsSync(srcDir)) {
      console.warn(`Directory not found: ${srcDir}`);
      continue;
    }

    fs.mkdirSync(destDir, { recursive: true });
    const files = fs.readdirSync(srcDir).filter(f => f.endsWith('.json'));

    for (const file of files) {
      const filePath = path.join(srcDir, file);
      const baseName = path.basename(file, '.json');
      const destPath = path.join(destDir, `${baseName}.ts`);

      try {
        const ts = await compileFromFile(filePath, {
          bannerComment: '/* eslint-disable */\n/**\n * This file was automatically generated from JSON Schema.\n * Do not modify it manually.\n */',
        });
        fs.writeFileSync(destPath, ts, 'utf-8');
        console.log(`  ✅ Generated: ${dir}/${baseName}.ts`);
        allExports.push(`export * from './${dir}/${baseName}';`);
      } catch (err) {
        console.error(`  ❌ Error compiling ${file}:`, err);
      }
    }
  }

  // Create barrel index.ts
  const indexPath = path.join(TARGET_TYPES_DIR, 'index.ts');
  fs.writeFileSync(indexPath, allExports.join('\n') + '\n', 'utf-8');
  console.log('✨ Type generation complete!');
}

generateTypes().catch((err) => {
  console.error('Fatal error during codegen:', err);
  process.exit(1);
});
