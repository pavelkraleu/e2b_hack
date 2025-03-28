import { Sandbox } from "@e2b/code-interpreter";
import * as fs from "fs";
import * as path from "path";
import * as dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();

async function analyzeParcels(filePath?: string) {
  const templateId = "9goyjdatvjzr0jxgp2tq";

  // Create a new sandbox with environment variables
  const sandbox = await Sandbox.create(templateId, {
    apiKey: process.env.E2B_API_KEY,
    envs: {
      OPENAI_API_KEY: process.env.OPENAI_API_KEY || "",
    },
  });

  try {
    // Copy the Python file
    const scriptContent = fs.readFileSync("analyze_parcels.py");
    await sandbox.files.write("/home/user/analyze_parcels.py", scriptContent);

    // // Copy the input file
    if (filePath) {
      const inputContent = fs.readFileSync(filePath);
      await sandbox.files.write("/home/user/input.jsonl", inputContent);
    }

    // Install dependencies and set up TypeScript
    console.log("Installing dependencies...");
    await sandbox.commands.run("pip install openai");

    // Run the analysis script with ts-node
    console.log("Running analysis...");
    const result = await sandbox.commands.run(
      `python /home/user/analyze_parcels.py ${
        filePath ? "/home/user/input.jsonl" : "/app/data.csv"
      } /home/user/output.jsonl`,
      {
        timeoutMs: 1000 * 60 * 5,
      }
    );

    // Print stdout and stderr from the sandbox
    if (result.stdout) {
      console.log("\nScript output:");
      console.log(result.stdout);
    }
    if (result.stderr) {
      console.error("\nScript errors:");
      console.error(result.stderr);
    }

    // Read the results
    const outputContent = await sandbox.files.read("/home/user/output.jsonl");

    // Write results to local file
    const outputPath = "analyzed_parcels.jsonl";
    fs.writeFileSync(outputPath, outputContent, { encoding: "utf-8" });

    console.log(`\nAnalysis complete. Results written to ${outputPath}`);
  } finally {
    // Clean up the sandbox
    await sandbox.kill();
  }
}

// Main execution
const filePath = process.argv[2]; // optional, otherwise use the default data file

// Check for required environment variables
if (!process.env.E2B_API_KEY) {
  console.error("Please set the E2B_API_KEY environment variable in .env file");
  process.exit(1);
}

if (!process.env.OPENAI_API_KEY) {
  console.error(
    "Please set the OPENAI_API_KEY environment variable in .env file"
  );
  process.exit(1);
}

analyzeParcels(filePath).catch(console.error);
