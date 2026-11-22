/* Logotipo tipografico RINDEx con hoja vectorial sobre la x */

export function LogoRindex(): React.JSX.Element {
  return (
    <span className="logo-rindex" aria-label="RINDEx">
      RINDE
      <span className="logo-rindex-x-envoltura">
        x
        <svg
          className="logo-rindex-hoja"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M4 19C6 11 12 6 20 4C19 12 14 18 6 19C5.2 19.1 4.5 19.1 4 19Z"
            fill="currentColor"
          />
          <path
            d="M4.5 19C9 14.5 13 11 18.5 6.5"
            stroke="var(--color-superficie)"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
        </svg>
      </span>
    </span>
  );
}
