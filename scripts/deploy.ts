import { ethers } from "hardhat";

async function main() {
  console.log("Initiating FlashArbitrage deployment to Optimism Mainnet...");

  // Grab the deployer account
  const [deployer] = await ethers.getSigners();
  console.log(`Deploying contracts with the account: ${deployer.address}`);

  // Fetch and deploy the contract
  const flashArbitrage = await ethers.deployContract("FlashArbitrage");
  await flashArbitrage.waitForDeployment();

  console.log(`✅ FlashArbitrage successfully deployed to: ${flashArbitrage.target}`);
  console.log("Remember to update config/constants.py with this new contract address.");
}

main().catch((error) => {
  console.error("Deployment failed:", error);
  process.exitCode = 1;
});
