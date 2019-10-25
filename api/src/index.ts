import * as nconf from "nconf";
import { init } from "./server";

nconf
  .argv()
  .env()
  .file({ file: "config/secret.json" })
  .defaults({
    database: {
      host: "scholar-reader.cjc2varstph5.us-east-2.rds.amazonaws.com",
      port: 5432,
      database: "postgres",
      user: "postgres"
    }
  });

init(nconf);