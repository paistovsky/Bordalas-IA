import { useMemo, useState } from "react";
import { initials } from "../lib/utils";

export default function PlayerAvatar({
  player,
  className = ""
}) {
  const candidates = useMemo(() => {
    const urls = [];
    const add = (url) => {
      if (url && !urls.includes(url)) {
        urls.push(url);
      }
    };

    // Fuente principal oficial de facto que usa Biwenger
    // en su propia interfaz:
    if (player?.id) {
      add(
        `https://cdn.biwenger.com/cdn-cgi/image/f=avif/i/p/${player.id}.png`
      );
    }

    // Después cualquier URL ya resuelta por backend.
    add(player?.biwenger_photo_url);
    add(player?.photo_url);

    // iconHero queda como fallback secundario.
    if (player?.icon_hero) {
      const value = String(player.icon_hero).trim();

      if (/^https?:\/\//i.test(value)) {
        add(value);
      } else {
        const clean = value.replace(/^\/+/, "");
        add(`https://cdn.biwenger.com/${clean}`);
      }
    }

    return urls;
  }, [player]);

  const [index, setIndex] = useState(0);
  const current = candidates[index];

  if (!current) {
    return (
      <div
        className={
          `player-avatar player-avatar-fallback ${className}`
        }
      >
        {initials(player?.name)}
      </div>
    );
  }

  return (
    <div className={`player-avatar ${className}`}>
      <img
        src={current}
        alt={player?.name || ""}
        onError={() => setIndex((i) => i + 1)}
      />
    </div>
  );
}
