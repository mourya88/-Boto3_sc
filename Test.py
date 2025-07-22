
{
  "name": "uka-client-react",
  "version": "1.0.0",
  "description": "React app with custom build logic for Barclays CI",
  "scripts": {
    "build": "npm run build-aws",        // 👈 Central pipeline will run this
    "build-aws": "node scripts/build-aws.js",
    "movebuild": "node scripts/movebuild.js",
    "start": "react-scripts start",
    "test": "react-scripts test",
    "lint": "eslint ./src",
    "format": "prettier --write ."
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "eslint": "^8.50.0",
    "prettier": "^3.2.4"
  }
}
Since you’ve not modified the pipeline, and npm run build is still present, the central template will not reject or block this setup.
