const p = { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true }
export const Check = (props) => <svg {...p} {...props}><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
export const Calendar = (props) => <svg {...p} {...props}><rect x="3.5" y="5" width="17" height="15" rx="3" /><path d="M8 3v4M16 3v4M3.5 10h17" /></svg>
export const Cross = (props) => <svg {...p} {...props}><path d="M6 6l12 12M18 6L6 18" /></svg>
export const Person = (props) => <svg {...p} {...props}><circle cx="12" cy="8" r="3.5" /><path d="M5 20c.8-3.6 3.5-5.5 7-5.5s6.2 1.9 7 5.5" /></svg>
export const Plus = (props) => <svg {...p} {...props}><path d="M12 5v14M5 12h14" /></svg>
export const Send = (props) => <svg {...p} {...props}><path d="M5 12l14-7-5 14-2.5-5.5L5 12z" /></svg>
export const Pin = (props) => <svg {...p} {...props}><path d="M12 21s7-6.2 7-11.5A7 7 0 005 9.5C5 14.8 12 21 12 21z" /><circle cx="12" cy="9.5" r="2.5" /></svg>
export const Alert = (props) => <svg {...p} {...props}><circle cx="12" cy="12" r="9" /><path d="M12 7.5v5M12 16v.2" /></svg>
export const Menu = (props) => <svg {...p} {...props}><path d="M4 7h16M4 12h16M4 17h16" /></svg>
export const Retry = (props) => <svg {...p} {...props}><path d="M4 12a8 8 0 1114 5.3M4 12V6.5M4 12h5.5" /></svg>
export const Logo = ({ size = 38 }) => (
  <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
    <rect width="40" height="40" rx="11" fill="#0f6b63" />
    <path d="M9 27h22" stroke="#bfe3de" strokeWidth="2" strokeLinecap="round" />
    <path d="M12.5 27a7.5 7.5 0 0115 0z" fill="#f6c453" />
    <path d="M20 12v3M11.5 15.5l2 2M28.5 15.5l-2 2" stroke="#f6c453" strokeWidth="2" strokeLinecap="round" />
  </svg>
)
