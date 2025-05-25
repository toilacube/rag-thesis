import ApiKeyInput from "./components/api-keys-input";
import ApiKeysTable from "./components/api-keys-table";
import { getAPIKeys } from "./utils/get-api-keys";

const APIKeys = async () => {
  const apiKeys = await getAPIKeys();

  return (
    <div className="container mx-auto py-10">
      <ApiKeyInput />

      <div className="rounded-md border">
        <ApiKeysTable initialApiKeys={apiKeys} />
      </div>
    </div>
  );
};

export default APIKeys;
