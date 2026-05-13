import { Container } from "@cloudflare/containers";
import { env } from "cloudflare:workers";

export class VipPaymentBotContainer extends Container {
  defaultPort = 8080;
  requiredPorts = [8080];
  sleepAfter = "24h";
  envVars = {
    BOT_TOKEN: env.BOT_TOKEN,
    ADMIN_IDS: env.ADMIN_IDS,
    TELETHON_API_ID: env.TELETHON_API_ID,
    TELETHON_API_HASH: env.TELETHON_API_HASH,
    TELETHON_SESSION_STRING: env.TELETHON_SESSION_STRING,
    VIP_GROUP_ID: env.VIP_GROUP_ID,
    SAWERIA_USERNAME: env.SAWERIA_USERNAME,
    PAYMENT_AMOUNT: env.PAYMENT_AMOUNT,
    PAYMENT_EMAIL: env.PAYMENT_EMAIL,
    PAYMENT_EXPIRE_MINUTES: env.PAYMENT_EXPIRE_MINUTES,
    PAYMENT_CHECK_INTERVAL_SECONDS: env.PAYMENT_CHECK_INTERVAL_SECONDS,
    VIP_INVITE_EXPIRE_HOURS: env.VIP_INVITE_EXPIRE_HOURS,
    VIP_INVITE_USAGE_LIMIT: env.VIP_INVITE_USAGE_LIMIT,
    DB_PATH: env.DB_PATH,
    LOG_LEVEL: env.LOG_LEVEL,
    HEALTH_HOST: "0.0.0.0",
    HEALTH_PORT: "8080"
  };
}

function unauthorized() {
  return new Response("Unauthorized", { status: 401 });
}

function checkBootToken(request) {
  const configured = env.CLOUDFLARE_BOOT_TOKEN;
  if (!configured) {
    return false;
  }
  const provided = request.headers.get("x-boot-token");
  return provided === configured;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const container = env.VIP_PAYMENT_BOT.getByName("singleton");

    if (url.pathname === "/start" || url.pathname === "/health") {
      if (!checkBootToken(request)) {
        return unauthorized();
      }
      return container.fetch("http://container/health");
    }

    return new Response(
      "VIP payment bot container. Use /start or /health with x-boot-token.",
      { status: 200 }
    );
  },

  async scheduled(controller, env, ctx) {
    const container = env.VIP_PAYMENT_BOT.getByName("singleton");
    ctx.waitUntil(container.fetch("http://container/health"));
  }
};
