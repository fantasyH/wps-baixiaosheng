import { useRef, useEffect, useState } from 'react';

/**
 * ShineButton — 按钮划过光效（react-bits StarBorder 风格）
 */
export default function ShineButton({ children, className = '', onClick, disabled }) {
  const ref = useRef(null);
  const [shinePos, setShinePos] = useState(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const handleMove = (e) => {
      const rect = el.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      setShinePos({ x, y });
    };

    const handleLeave = () => setShinePos(null);

    el.addEventListener('mousemove', handleMove);
    el.addEventListener('mouseleave', handleLeave);
    return () => {
      el.removeEventListener('mousemove', handleMove);
      el.removeEventListener('mouseleave', handleLeave);
    };
  }, []);

  return (
    <button
      ref={ref}
      onClick={onClick}
      disabled={disabled}
      className={className}
      style={{
        position: 'relative',
        overflow: 'hidden',
        isolation: 'isolate',
      }}
    >
      {children}
      {shinePos && (
        <span
          style={{
            position: 'absolute',
            pointerEvents: 'none',
            top: 0, left: 0, right: 0, bottom: 0,
            background: `radial-gradient(circle at ${shinePos.x}% ${shinePos.y}%, rgba(255,255,255,0.25), transparent 60%)`,
            zIndex: 1,
          }}
        />
      )}
    </button>
  );
}