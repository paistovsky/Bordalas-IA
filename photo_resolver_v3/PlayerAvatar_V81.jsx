import { useMemo, useState } from "react";
import { initials } from "../lib/utils";

export default function PlayerAvatar({ player, className = "" }) {
  const candidates = useMemo(() => {
    const urls = [];
    const add = (url) => {
      if (url && !urls.includes(url)) urls.push(url);
    };

    add(player?.biwenger_photo_url);

    if (player?.icon_hero) {
      const value = String(player.icon_hero).trim();
      if (/^https?:\/\//i.test(value)) {
        add(value);
      } else {
        const clean = value.replace(/^\/+/, "");
        add(`https://cdn.biwenger.com/${clean}`);
        add(`https://biwenger.as.com/${clean}`);
      }
    }

    add(player?.photo_url);
    add(player?.api_photo_url);

    if (player?.api_football_id) {
      add(`https://media.api-sports.io/football/players/${player.api_football_id}.png`);
    }

    return urls;
  }, [player]);

  const [index, setIndex] = useState(0);
  const current = candidates[index];

  if (!current) {
    return (
      <div className={`player-avatar player-avatar-fallback ${className}`}>
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
