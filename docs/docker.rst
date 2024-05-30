Docker
======

To run PyEconomics using Docker, follow these steps:

1. **Configure the .env File**:
   Create a `.env` file in the root directory of pyeconomics with the following
   content:

   .. code-block:: text

      FRED_API_KEY=your_fred_api_key_here

2. **Build the Docker Image**:
   Navigate to your pyeconomics root directory and run the following command to
   build the Docker image:

   .. code-block:: shell

      docker build -t pyeconomics .

3. **Run the Docker Container**:
   Run a container from your custom Docker image:

   .. code-block:: shell

      docker run --env-file .env -p 8888:8888 -it --rm pyeconomics

   This will start a JupyterLab instance with the specified notebook open.

4. **Access JupyterLab**:
   In the command prompt output, you will see something like this:

   .. code-block:: text

      To access the server, open this file in a browser:
          file:///root/.local/share/jupyter/runtime/jpserver-1-open.html
      Or copy and paste one of these URLs:
          http://e99fe8b9fbb5:8888/lab/tree/monetary_policy_rules/monetary_policy_rules.ipynb?token=your_token_here
          http://127.0.0.1:8888/lab/tree/monetary_policy_rules/monetary_policy_rules.ipynb?token=your_token_here

   To open JupyterLab in your browser, hold the CTRL button and click the link
   starting with: ``http://127.0.0.1:8888``. Ignore the other links.

By using Docker, you ensure a consistent environment for running and testing
PyEconomics.
