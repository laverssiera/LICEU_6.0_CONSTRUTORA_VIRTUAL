import "../styles/globals.css";
import JohnWidget from "../components/JohnWidget";

export default function App({ Component, pageProps }) {
  return (
    <div className="app-root">
      <Component {...pageProps} />
      <JohnWidget />
    </div>
  );
}
