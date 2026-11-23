/* Logotipo tipografico RINDEx en identidad de la familia x */

interface PropsLogoRindex {
  sobreOscuro?: boolean;
}

export function LogoRindex({ sobreOscuro = false }: PropsLogoRindex): React.JSX.Element {
  return (
    <span
      className={sobreOscuro ? "logo-rindex logo-rindex-oscuro" : "logo-rindex"}
      aria-label="RINDEx"
    >
      <span className="logo-rindex-base">RINDE</span>
      <span className="logo-rindex-x" aria-hidden="true">
        x
      </span>
    </span>
  );
}
