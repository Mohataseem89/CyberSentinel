export default function Card({ 
  children, 
  className = '', 
  hover = false,
  padding = 'default'
}) {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    default: 'p-6',
    lg: 'p-8'
  };

  return (
    <div className={`card ${hover ? 'card-hover' : ''} ${paddingClasses[padding]} ${className}`}>
      {children}
    </div>
  );
}
