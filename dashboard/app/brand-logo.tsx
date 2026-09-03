type BrandLogoProps = {
  variant?: "horizontal" | "symbol";
  className?: string;
};

const variants = {
  horizontal: { src: "/brand/smart-environment-horizontal.png", width: 363, height: 154 },
  symbol: { src: "/brand/smart-environment-symbol.png", width: 167, height: 137 },
};

export function BrandLogo({ variant = "horizontal", className = "" }: BrandLogoProps) {
  const image = variants[variant];
  return (
    // eslint-disable-next-line @next/next/no-img-element -- small local brand assets, preserved exactly as supplied
    <img
      className={`brand-image ${className}`.trim()}
      src={image.src}
      width={image.width}
      height={image.height}
      alt="Smart Environment"
      decoding="async"
      draggable={false}
    />
  );
}
