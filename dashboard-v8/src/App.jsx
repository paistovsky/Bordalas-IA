import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";
import KpiStrip from "./components/KpiStrip";
import SelectorDisposicion from "./components/SelectorDisposicion";
import { useDisposicion } from "./lib/disposicion";
import HomePage from "./pages/HomePage";
import PlanPage from "./pages/PlanPage";
import MercadoPage from "./pages/MercadoPage";
import PlantillaPage from "./pages/PlantillaPage";
import LigaPage from "./pages/LigaPage";
import TallerPage from "./pages/TallerPage";
import MarketPage from "./pages/MarketPage";
import BrainPage from "./pages/BrainPage";
import SquadPage from "./pages/SquadPage";
import LeaguePage from "./pages/LeaguePage";
import MarcadorPage from "./pages/MarcadorPage";
import AuditPage from "./pages/AuditPage";
import { fetchStatus, normalizeStatus } from "./lib/status";
import { ago } from "./lib/utils";
import { madridNaiveAUTC, minutosDeLaFoto } from "./lib/relojes";

/* LOS SEIS MENÚS (30/09/2026)
 *
 * INICIO se queda como estaba. Los demás se hicieron desde cero,
 * cada uno con una pregunta: EL PLAN (¿qué va a hacer Pepe y con
 * qué dinero?), MERCADO (¿qué nos hace ganar hoy?), PLANTILLA
 * (¿cómo está el equipo?), LIGA (¿quién nos puede quitar el
 * título?). MARCADOR se repartió entre PLANTILLA y LIGA.
 *
 * Todo lo técnico -las pantallas de antes, enteras, con la
 * auditoría y el diagnóstico- vive cerrado en el TALLER. */
const TITLES = {
  home: "INICIO",
  plan: "EL PLAN",
  market: "MERCADO",
  squad: "PLANTILLA",
  league: "LIGA",
  taller: "TALLER"
};

export default function App() {
  const [page, setPage] = useState("home");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const raw = await fetchStatus();
        if (!cancelled) {
          setData(normalizeStatus(raw));
          setError("");
        }
      } catch (err) {
        if (!cancelled) setError(err.message || String(err));
      }
    };

    load();
    const timer = setInterval(load, 60_000);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  // EL RELOJ DE LA PASTILLA, ARRIBA DEL TODO (10/09/2026)
  //
  // Estaba DEBAJO de los dos `return` de abajo, y eso tumbo la
  // pagina entera: sin datos se ejecutaban cuatro hooks y con
  // datos seis. React cuenta los hooks por orden y en el mismo
  // numero cada vez -asi sabe cual es cual-, asi que al aparecer
  // dos de la nada aborta el arbol completo. Pantalla en blanco,
  // error #310.
  //
  // La regla no admite matices: los hooks van SIEMPRE arriba,
  // antes de cualquier return y fuera de todo `if`. Lo
  // condicional es lo que se PINTA, nunca el hook.
  const [ahora, setAhora] = useState(() => new Date());

  useEffect(() => {
    const t = setInterval(() => setAhora(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // MÓVIL O PC. También arriba, con los demás hooks: el selector
  // se ve y se recuerda aunque todavía no hayan llegado los datos.
  const disposicion = useDisposicion();

  if (error && !data) {
    return <div className="screen err">NO SE PUDO CARGAR BORDALÁS IA · {error}</div>;
  }

  if (!data) {
    return <div className="screen">CARGANDO BORDALÁS IA…</div>;
  }

  // Las pantallas de antes, enteras, en los cajones del taller.
  // No se pintan hasta que se abre su cajón.
  const cajones = [
    {
      titulo: "Auditoría y diagnóstico",
      detalle: "la salud de Pepe, sus comprobaciones y las pujas por dentro",
      contenido: <AuditPage data={data} error={error} />
    },
    {
      titulo: "El mercado por dentro",
      detalle: "reloj, caja, objetivos, publicaciones y la liga entera",
      contenido: <MarketPage data={data} />
    },
    {
      titulo: "Cómo piensa Pepe",
      detalle: "planes, doctrina, rivales, calendario, ojeador y solvencia",
      contenido: <BrainPage data={data} />
    },
    {
      titulo: "La plantilla al detalle",
      detalle: "el campo, la tabla, las plantillas rivales, la vara y el orden de venta",
      contenido: <SquadPage data={data} />
    },
    {
      titulo: "La liga al detalle",
      detalle: "la tabla de inteligencia y el libro de operaciones",
      contenido: <LeaguePage data={data} />
    },
    {
      titulo: "El marcador al detalle",
      detalle: "la nota del once jornada a jornada",
      contenido: <MarcadorPage data={data} />
    }
  ];

  const pages = {
    home: <HomePage data={data} />,
    plan: <PlanPage data={data} />,
    market: <MercadoPage data={data} />,
    squad: <PlantillaPage data={data} />,
    league: <LigaPage data={data} />,
    taller: <TallerPage cajones={cajones} />
  };

  const minutosFoto = minutosDeLaFoto(data.meta.generated_at);

  // Pepe parado = la ultima vuelta tiene mas de tres horas. Es lo
  // UNICO que se pinta en rojo arriba.
  const parado = minutosFoto != null && minutosFoto > 180;

  const haceTexto =
    minutosFoto == null
      ? ago(data.meta.generated_at)
      : minutosFoto < 60
      ? `${minutosFoto} min`
      : minutosFoto < 48 * 60
      ? `${Math.floor(minutosFoto / 60)} h`
      : `${Math.floor(minutosFoto / 1440)} días`;

  // La hora de Madrid, leida con su zona: `generated_at` viene sin
  // zona y es hora de Madrid.
  const vueltaISO = madridNaiveAUTC(data.meta.generated_at);
  const horaDeLaVuelta = vueltaISO
    ? new Intl.DateTimeFormat("es-ES", {
        timeZone: "Europe/Madrid",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
      }).format(new Date(vueltaISO))
    : "sin dato";

  return (
    <>
      <Sidebar page={page} setPage={setPage} data={data} />

      <main>
        <div className="page-head">
          <h1>{TITLES[page]}</h1>
          <span className="tag">
            JORNADA {data.summary.target_matchday ?? "—"}
          </span>
          <SelectorDisposicion {...disposicion} />
        </div>

        {/* UNA LÍNEA Y NADA MÁS (30/09/2026)

            «Los avisos siguen saliendo.» Aquí había una línea que
            contaba avisos y se desplegaba. Ahora dice sólo cuándo
            fue la última vuelta de Pepe: verde, y roja únicamente
            si lleva más de tres horas sin vuelta. Todo lo que había
            debajo -edad de la foto, racha, sentidos, caja de los
            rivales, XI de Biwenger, cuadre, titularidad- vive
            plegado en DIAGNÓSTICO, en el TALLER. */}
        <div className={`estado ${parado ? "parado" : "ok"}`}>
          <span className="estado-punto" aria-hidden="true" />
          Última vuelta de Pepe: {horaDeLaVuelta}
          {parado ? ` · hace ${haceTexto}` : ""}
        </div>

        {/* LA TIRA, SOLO EN INICIO (30/09/2026). Cada página
            contesta su pregunta arriba; repetir seis tarjetas
            encima de todas empujaba la respuesta fuera de la
            pantalla del móvil. */}
        {page === "home" && <KpiStrip data={data} />}

        {pages[page]}

        <p className="note">
          Todos los números salen de dashboard/data/status.json. Nada inventado.
        </p>
      </main>
    </>
  );
}
