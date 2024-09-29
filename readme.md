# GDPR Obfuscator Project

## Overview

The GDPR Obfuscator Project is a general-purpose tool designed to process data ingested to AWS and intercept personally identifiable information (PII). This project aims to comply with GDPR regulations by anonymizing sensitive data in bulk data analysis scenarios, ensuring that all information stored does not identify individuals.

## Context

This tool is intended for the **Skills Bootcamp: Software Developer/Coding Skills Graduates** in a **Data Engineering** context. The primary goal is to create a library module that obfuscates PII from CSV files stored in AWS S3.

## Assumptions and Prerequisites

- Data is stored in CSV format in S3.
- Fields containing GDPR-sensitive data will be known and provided in advance.
- Data records will include a primary key.

## High-Level Desired Outcome

The tool will be provided with the S3 location of a file containing sensitive information and the names of the affected fields. It will create a new file or byte stream object that contains an exact copy of the input file but with the sensitive data replaced by obfuscated strings. The calling procedure will handle saving the output to its destination.

### Example Input

The tool will be invoked with a JSON string containing:

```json
{"bucket_name": "bucket_name",
"s3_file_path": "data.csv",
"pii_fields": ["Name", "Email Address"]}
```

### Example Input CSV File

```plaintext
User ID,Name,Graduation Date,Email Address
1001,Alice Johnson,2022-05-15,alice.johnson1001@example.com
1002,Bob Smith,2023-06-20,bob.smith1002@example.com
1003,Carol Davis,2022-08-30,carol.davis1003@example.com
```

### Example Output

The output will be a byte stream representation of a file that looks like this:

```plaintext
User ID,Name,Graduation Date,Email Address
1001,***,2022-05-15,***
1002,***,2023-06-20,***
1003,***,2022-08-30,***
```

## Non-Functional Requirements

- The tool should be written in Python, PEP-8 compliant, and tested for security vulnerabilities.
- The code must include documentation.
- No credentials should be recorded in the code.
- The total size of the module should not exceed the memory limits for Python Lambda dependencies.

## Performance Criteria

- The tool should handle files of up to 1MB with a runtime of less than 1 minute.

## Possible Extensions

The MVP could be extended to support other file formats, primarily JSON and Parquet, while maintaining compatibility with the input formats.

## Tech Stack

- **Programming Language**: Python
- **AWS SDK**: Boto3
- **Testing Tools**: Pytest
- **Deployment**: AWS Lambda

## Usage

Although the tool is intended to function as a library, demonstration of its use can be done through command-line invocation.

# Opening a Free AWS Account

Amazon Web Services (AWS) offers a free tier that allows you to access various services without incurring costs for a limited period. Follow these steps to create your free AWS account:

## Step 1: Go to the AWS Free Tier Page

1. Open your web browser and navigate to the [AWS Free Tier page](https://aws.amazon.com/free/).

## Step 2: Click on "Create a Free Account"

2. Click on the **Create a Free Account** button located in the center of the page.

## Cloning the Repository

Before setting up AWS access keys, you need to clone the repository to your local machine. Follow these steps:

1. **Open Your Terminal or Command Prompt:**
   - On your local machine, open your terminal (Linux/Mac) or command prompt (Windows).

2. **Clone the Repository:**
   - Use the following command to clone the repository:
     ```bash
     git clone https://github.com/A-Waterhouse/GDPR
     ```
   

3. **Navigate to the Cloned Repository:**
   - After cloning, change into the directory of the cloned repository:

After cloning the repository, you can proceed to set up AWS access keys in GitHub.

## Setting Up AWS Access Keys in GitHub

To enable the project to interact with AWS services, you need to configure AWS access keys in your GitHub repository. Follow these steps to set up the necessary secrets:

1. **Navigate to the GDPR Repository:**
   - Go to the GitHub website and open the repository.

2. **Access Repository Settings:**
   - Click on the `Settings` tab located in the upper right corner of your repository page.

3. **Select Secrets and Variables:**
   - On the left sidebar, click on `Secrets and variables`.
   - Then click on `Actions` to manage secrets for GitHub Actions.

4. **Add New Repository Secret:**
   - Click on the `New repository secret` button.

5. **Create AWS Access Key:**
   - If you haven’t done so already, go to the AWS Management Console.
   - Navigate to the IAM (Identity and Access Management) service.
   - Click on `Users`, select your user, and go to the `Security credentials` tab.
   - Click on `Create access key` and note down your Access Key ID and Secret Access Key.

6. **Enter the Secrets:**
   - In the `Name` field, enter `AWS_ACCESS_KEY`.
   - In the `Value` field, paste your Access Key ID from AWS.
   - Click on `Add secret`.
   - Repeat the process to create another secret:
     - In the `Name` field, enter `AWS_SECRET`.
     - In the `Value` field, paste your Secret Access Key from AWS.
     - Click on `Add secret`.

Once these secrets are set up, your GitHub Actions workflows will have the necessary permissions to access AWS resources securely.



