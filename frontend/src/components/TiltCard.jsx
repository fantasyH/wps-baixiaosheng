import { useRef, useEffect, useState } from 'react';

/**
 * TiltCard — 鼠标悬停时 3D 倾斜效果（react-bits 风格）
 */
export default function TiltCard({ children, className = '', maxTilt = 8 }) {
  const ref = useRef(null);
  const [style, setStyle] = useState({});

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const handleMove = (e) => {
      const rect = el.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      setStyle({
        transform: `perspective(600px) rotateX(${-y * maxTilt}deg) rotateY(${x * maxTilt}deg) scale3d(1.01, 1.01, 1.01)`,
      });
    };

    const handleLeave = () => {
      setStyle({ transform: 'perspective(600px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)' });
    };

    el.addEventListener('mousemove', handleMove);
    el.addEventListener('mouseleave', handleLeave);
    return () => {
      el.removeEventListener('mousemove', handleMove);
      el.removeEventListener('mouseleave', handleLeave);
    };
  }, [maxTilt]);

  return (
    <div ref={ref} className={`tilt-card ${className}`} style={{ ...style, transition: 'transform 0.1s ease-out' }}>
      {children}
    </div>
  );
}
