# AWS Cloud Cost Monitor 📊☁️

Welcome! This is a simple, beautiful tool designed to help you keep track of your AWS costs so you never get surprised by a high bill. 

It tracks your daily spending, shows everything on a modern dark-themed dashboard, and sends you an email alert if you go over your budget.

---

## ✨ Key Features
* **Friendly Dashboard**: A clean, dark-mode visual interface to see where your money is going (EC2, Lambda, S3, etc.).
* **Smart Alerting**: Set a budget (e.g., $100/month) and get an email the second your costs cross that limit.
* **Completely Serverless**: Built using modern AWS technology (Lambda functions and DynamoDB) so it costs virtually nothing to run.

---

## 🛠️ Quick Start (Run it locally)

You can run this entire application on your computer without connecting to your real AWS account! 

### 1. Install Dependencies
Get all the project dependencies installed:
```bash
make install
```

### 2. Start the Database & Local API
This will set up a local simulated database, fill it with 30 days of mock cost data, and start a local API server:
```bash
make local
```

### 3. Start the Dashboard
Now, open another terminal window and start the visual dashboard:
```bash
cd dashboard
npm start
```
Go to **[http://localhost:3000](http://localhost:3000)** in your browser to see your cost graphs!

---

## 🚀 Deploying to AWS (Make it live)

When you're ready to deploy this to your real AWS account:

1. **Deploy the stack**:
   ```bash
   make build
   make deploy
   ```
   *The installer will ask you for your **email address** (for cost alerts) and your **monthly budget threshold**.*

2. **Load initial settings**:
   ```bash
   make seed
   ```

3. **Tear down** (if you want to delete everything from your AWS account):
   ```bash
   make destroy
   ```

---

## 📂 Project Structure
* `/dashboard` - The React frontend dashboard website.
* `/src` - The backend Lambda functions that fetch and check cost metrics.
* `template.yaml` - The blueprint AWS SAM uses to set up your cloud infrastructure.
