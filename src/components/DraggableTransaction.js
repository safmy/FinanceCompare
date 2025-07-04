import React, { useState } from 'react';
import { format } from 'date-fns';

const DraggableTransaction = ({ transaction, onDragStart, onClick }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [longPressTimer, setLongPressTimer] = useState(null);
  const [isLongPress, setIsLongPress] = useState(false);

  const handleMouseDown = (e) => {
    // Start long press timer
    const timer = setTimeout(() => {
      setIsLongPress(true);
      // Trigger drag programmatically
      e.target.draggable = true;
    }, 500); // 500ms for long press
    setLongPressTimer(timer);
  };

  const handleMouseUp = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }
    if (!isLongPress) {
      onClick();
    }
    setIsLongPress(false);
  };

  const handleMouseLeave = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }
    setIsLongPress(false);
  };

  const handleDragStart = (e) => {
    if (!isLongPress) {
      e.preventDefault();
      return;
    }
    setIsDragging(true);
    onDragStart(transaction);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragEnd = () => {
    setIsDragging(false);
    setIsLongPress(false);
  };

  // Touch events for mobile
  const handleTouchStart = (e) => {
    const timer = setTimeout(() => {
      setIsLongPress(true);
      // Create a drag image
      const dragImage = e.target.cloneNode(true);
      dragImage.style.position = 'fixed';
      dragImage.style.pointerEvents = 'none';
      dragImage.style.opacity = '0.8';
      dragImage.style.zIndex = '9999';
      document.body.appendChild(dragImage);
      
      const touch = e.touches[0];
      dragImage.style.left = `${touch.clientX}px`;
      dragImage.style.top = `${touch.clientY}px`;
      
      // Store drag image reference
      e.target._dragImage = dragImage;
      onDragStart(transaction);
    }, 500);
    setLongPressTimer(timer);
  };

  const handleTouchMove = (e) => {
    if (isLongPress && e.target._dragImage) {
      const touch = e.touches[0];
      e.target._dragImage.style.left = `${touch.clientX - 50}px`;
      e.target._dragImage.style.top = `${touch.clientY - 20}px`;
    }
  };

  const handleTouchEnd = (e) => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }
    
    if (isLongPress && e.target._dragImage) {
      // Find element under touch point
      const touch = e.changedTouches[0];
      const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
      
      // Check if dropped on a category card
      const categoryCard = elementBelow?.closest('[data-category-drop]');
      if (categoryCard) {
        const category = categoryCard.getAttribute('data-category-drop');
        window.dispatchEvent(new CustomEvent('transaction-drop', {
          detail: { transaction, category }
        }));
      }
      
      // Clean up drag image
      document.body.removeChild(e.target._dragImage);
      e.target._dragImage = null;
    } else if (!isLongPress) {
      onClick();
    }
    
    setIsLongPress(false);
  };

  return (
    <tr
      className={`hover:bg-gray-50 cursor-pointer transition-all ${
        isDragging ? 'opacity-50' : ''
      } ${isLongPress ? 'bg-blue-50 shadow-lg' : ''}`}
      draggable={isLongPress}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseLeave}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        {transaction.date ? (
          (() => {
            try {
              return format(new Date(transaction.date), 'dd MMM yyyy');
            } catch (e) {
              return transaction.date;
            }
          })()
        ) : 'No date'}
      </td>
      <td className="px-6 py-4 text-sm text-gray-900">
        <div className="max-w-xs truncate" title={transaction.description}>
          {transaction.description}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
        <span className={transaction.amount < 0 ? 'text-red-600' : 'text-green-600'}>
          {transaction.amount < 0 ? '-' : '+'}£{Math.abs(transaction.amount).toFixed(2)}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        <span className="px-2 py-1 text-xs rounded-full bg-gray-100">
          {transaction.category}
        </span>
      </td>
    </tr>
  );
};

export default DraggableTransaction;