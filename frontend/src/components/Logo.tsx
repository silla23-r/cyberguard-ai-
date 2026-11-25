import React from "react";

interface LogoProps {
  className?: string;
  size?: number;
}

export const Logo: React.FC<LogoProps> = ({ className = "w-8 h-8", size = 32 }) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 100 100"
      fill="none"
      width={size}
      height={size}
      className={className}
      aria-label="CyberGuard Logo"
    >
      {/* Outer Shield Geometry forming 'C' */}
      <path
        d="M 50 14 
           L 80 14 
           L 80 32 
           L 66 32 
           L 66 26 
           L 50 26 
           L 26 26 
           L 26 50 
           C 26 68 50 82 50 82 
           C 50 82 74 68 74 50 
           L 74 44 
           L 86 44 
           L 86 50 
           C 86 74 50 90 50 90 
           C 50 90 14 74 14 50 
           L 14 14 
           Z"
        fill="currentColor"
      />
      {/* Central Secure Node */}
      <circle cx="50" cy="50" r="8" fill="#0284C7" />
    </svg>
  );
};
