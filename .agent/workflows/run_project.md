---
description: How to run the MathBank project
---

# Run MathBank Project

1.  **Setup Virtual Environment** (Recommended):
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Credentials**:
    - Ensure `credentials.json` exists in the root directory.
    - If not, copy `credentials_template.json` to `credentials.json` and update it with your users.
    ```bash
    cp credentials_template.json credentials.json
    ```
    - Add a user:
    ```bash
    python add_user.py <username> <password>
    ```

4.  **Run the Application**:
    ```bash
    python app.py
    ```

5.  **Access the Interface**:
    - Open your browser and navigate to `http://localhost:5000`.
    - Log in with the credentials defined in `credentials.json`.
