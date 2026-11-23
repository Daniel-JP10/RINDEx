import { preview } from "vite";

export default async function iniciarServidorPreview(): Promise<() => Promise<void>> {
  const servidor = await preview({
    preview: {
      host: "127.0.0.1",
      port: 4173,
      strictPort: true,
    },
  });

  return async () => {
    await new Promise<void>((resolve) => {
      servidor.httpServer.close(() => resolve());
    });
  };
}
