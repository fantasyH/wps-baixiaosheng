import { useEffect, useRef } from 'react';

/**
 * MagneticButton — 鼠标靠近时按钮跟随磁吸效果（react-bits 风格）
 */
export default function MagneticButton({ children, className = '', strength = 0.35, onClick }) {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const handleMove = (e) => {
      const rect = el.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      el.style.transform = `translate(${x * strength}px, ${y * strength}px)`;
    };

    const handleLeave = () => {
      el.style.transform = 'translate(0, 0)';
    };

    el.addEventListener('mousemove', handleMove);
    el.addEventListener('mouseleave', handleLeave);
    return () => {
      el.removeEventListener('mousemove', handleMove);
      el.removeEventListener('mouseleave', handleLeave);
    };
  }, [strength]);

  return (
    <button
      ref={ref}
      className={className}
      onClick={onClick}
      style={{ transition: 'transform 0.2s cubic-bezier(0.4,0,0.2,1)', willChange: 'transform' }}
    >
      {children}
    </button>
  );
}
