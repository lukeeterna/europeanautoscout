// ─── Asset module declarations (wrangler "Data" rule) ──────────────
// TTF files in assets/fonts/*.ttf are bundled as ArrayBuffer modules.
// Declared so TypeScript accepts the binary imports in pdf/contract-template.ts.

declare module '*.ttf' {
  const data: ArrayBuffer;
  export default data;
}
