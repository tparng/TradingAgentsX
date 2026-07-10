// Next.js only declares `*.module.css`; TypeScript 5.6+ flags plain stylesheet
// side-effect imports (e.g. `import "./globals.css"`) as ts(2882) without this.
declare module "*.css";
