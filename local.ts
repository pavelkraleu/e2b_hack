import { spawn } from "child_process";
import * as path from "path";
import * as dotenv from "dotenv";

// Load environment variables
dotenv.config();

async function runAnalysis(inputFile: string, outputFile: string) {
  console.log(`Starting local analysis of ${inputFile}...`);

  // Get the absolute path to the Python script
  const scriptPath = "analyze_parcels.py";

  // Create the Python process using the virtual environment's Python
  const pythonProcess = spawn(
    "./venv/bin/python3",
    [scriptPath, inputFile, outputFile],
    {
      stdio: "inherit", // This will forward all output to the console
      env: {
        ...process.env, // Pass through all environment variables
        PYTHONUNBUFFERED: "1", // Ensure Python output is not buffered
      },
    }
  );

  // Handle process events
  return new Promise((resolve, reject) => {
    pythonProcess.on("close", (code) => {
      if (code === 0) {
        console.log("Analysis completed successfully");
        resolve(undefined);
      } else {
        console.error(`Analysis failed with code ${code}`);
        reject(new Error(`Process exited with code ${code}`));
      }
    });

    pythonProcess.on("error", (err) => {
      console.error("Failed to start Python process:", err);
      reject(err);
    });
  });
}

// Main execution
const inputFile = process.argv[2];
const outputFile = process.argv[3];

if (!inputFile || !outputFile) {
  console.error("Usage: tsx local.ts input.jsonl output.jsonl");
  process.exit(1);
}

// Run the analysis
runAnalysis(inputFile, outputFile).catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
