import { useEffect, useState, useRef } from 'react';

/**
 * AnimatedText — 逐字/逐词动画显示文本（react-bits 风格）
 * mode: 'word' | 'char' | 'blur'
 */
export default function AnimatedText({ 
  text, 
  mode = 'word', 
  className = '',
  delay = 0.05,
  stagger = true,
}) {
  const [visible, setVisible] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  const items = mode === 'word' ? text.split(' ') : text.split('');

  return (
    <span ref={ref} className={`inline-flex flex-wrap ${className}`}>
      {items.map((item, i) => (
        <span
          key={i}
          className={mode === 'char' ? '' : 'mr-[0.25em]'}
          style={{
            display: 'inline-block',
            opacity: visible ? 1 : 0,
            transform: visible ? 'translateY(0)' : 'translateY(12px)',
            filter: visible ? 'blur(0)' : 'blur(4px)',
            transition: `all 0.5s cubic-bezier(0.4,0,0.2,1) ${stagger ? i * delay : 0}s`,
          }}
        >
          {mode === 'word' ? (i === items.length - 1 ? item : item + '\u00A0') : item}
        </span>
      ))}
    </span>
  );
}
