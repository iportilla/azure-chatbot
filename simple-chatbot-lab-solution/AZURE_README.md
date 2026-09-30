# Connecting the Simple Chatbot to Azure Bot Service

This guide registers the chatbot with Azure Bot Service so you can reach it from Web Chat, Teams and other channels. It also covers the most common setup error.

> You don't need Azure to try the bot. Run `python -m src.main` and chat with it through the Microsoft 365 Agents Playground (`teamsapptester`), as described in [README.md](README.md).

## Troubleshooting: "AAD App Creation Failed. Please check your AAD permissions."

When you create an Azure Bot with **Create new Microsoft App ID**, the portal tries to register a new app in Microsoft Entra ID (Azure AD). That error means your account isn't allowed to register apps in the tenant. Common causes:

- You signed in with a personal Microsoft account or as a guest.
- A tenant admin has set **Users can register applications** to **No**.

The fix is to register the app yourself (step 1), then create the bot with **Use existing app registration** (step 2).

## Step 1: Register the app in Entra ID

### Portal

1. In the Azure portal, open **Microsoft Entra ID → App registrations → New registration**.
1. Fill in:
   - **Name:** `simple-chatbot`
   - **Supported account types:** *Accounts in this organizational directory only* (single tenant)
1. Select **Register**.
1. On the overview page, copy the **Application (client) ID** and the **Directory (tenant) ID**.
1. Open **Certificates & secrets → New client secret**, add it, and copy the secret's **Value** (not the Secret ID). The value is shown only once.

### Azure CLI

Create the app and print its client ID:

```bash
az ad app create --display-name simple-chatbot --sign-in-audience AzureADMyOrg --query appId -o tsv
```

Create a client secret and print its value:

```bash
az ad app credential reset --id <APP_ID> --query password -o tsv
```

Print your tenant ID:

```bash
az account show --query tenantId -o tsv
```

### If registration fails here too

Your tenant blocks app registration entirely. You can:

- ask a tenant admin to give you the **Application Developer** role,
- ask a tenant admin to register the app and send you the client ID, tenant ID and secret, or
- use a free Azure subscription with a tenant where you're the admin.

## Step 2: Create the Azure Bot

### Portal

1. Create an **Azure Bot** resource.
1. Under **Microsoft App ID**:
   - **Type of App:** Single Tenant
   - **Creation type:** **Use existing app registration**
   - Paste the **App ID** and **Tenant ID** from step 1.
1. Select **Review + create**.

### Azure CLI

```bash
az bot create --resource-group <RG> --name <BOT_NAME> --app-type SingleTenant --appid <APP_ID> --tenant-id <TENANT_ID>
```

> The **User-Assigned Managed Identity** bot type doesn't need an app registration, but it only works when the code runs inside Azure (for example App Service). It won't work for local development.

## Step 3: Configure the sample

1. Rename `env.TEMPLATE` to `.env`.
1. Uncomment the three lines and fill them in:

   ```
   CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=<APP_ID>
   CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=<SECRET_VALUE>
   CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=<TENANT_ID>
   ```

When `CLIENTID` is set, anonymous mode turns off and every request must carry a valid token. At that point the Agents Playground can no longer connect without credentials.

Don't commit `.env`; it contains your secret.

## Step 4: Expose the bot with a dev tunnel

1. Install [dev tunnels](https://learn.microsoft.com/azure/developer/dev-tunnels/get-started) and sign in:

   ```bash
   devtunnel user login
   ```

1. Host a tunnel to the bot's port:

   ```bash
   devtunnel host -p 3978 --allow-anonymous
   ```

1. Copy the URL shown after **Connect via browser:**.
1. In the Azure Bot resource, open **Settings → Configuration** and set **Messaging endpoint** to `{tunnel-url}/api/messages`. Select **Apply**.

## Step 5: Run and test

1. Start the bot:

   ```bash
   python -m src.main
   ```

1. In the Azure Bot resource, open **Test in Web Chat** and send `hello` or `/help`.

## Common problems

| Symptom | Likely cause |
| --- | --- |
| Requests are rejected with `401` | The client ID or tenant ID in `.env` doesn't match the Azure Bot |
| The bot receives messages but its replies fail with an authentication error | Wrong client secret in `.env`, or the secret's ID was used instead of its value, or the secret has expired |
| Web Chat shows nothing and the bot logs no requests | Messaging endpoint is wrong, missing `/api/messages`, or the tunnel has stopped |
| Tunnel URL changed | Update the messaging endpoint; a new tunnel gets a new URL unless you create a persistent one |
| Bot app type and registration don't match | Both must be single tenant |
