require('dotenv').config({ path: 'env/.env.dev' });
const { exec } = require('child_process');
const JWTGenerator = require('./jwtGenerator');

const jwt = new JWTGenerator();
const jwtToken = jwt.getToken();

const curlCmd = `curl -X POST ${process.env.AGENT_ENDPOINT} \
-H "X-Snowflake-Authorization-Token-Type: KEYPAIR_JWT" \
-H "Authorization: Bearer ${jwtToken}" \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
-d '{
  "model": "claude-3-5-sonnet",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Which are the top revenue generating opportunities?"
        }
      ]
    }
  ]
}'`;

exec(curlCmd, (err, stdout, stderr) => {
  if (err) {
    console.error('❌ curl error:', err.message);
    return;
  }
  console.log('✅ Cortex Agents response:\n\n', stdout);
});