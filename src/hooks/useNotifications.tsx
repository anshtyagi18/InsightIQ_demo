
import { useState } from 'react';

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success';
  timestamp: Date;
  read: boolean;
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([
    {
      id: '1',
      title: 'Data Sync Complete',
      message: 'All data sources have been synchronized successfully.',
      type: 'success',
      timestamp: new Date(Date.now() - 1000 * 60 * 30),
      read: false
    },
    {
      id: '2',
      title: 'Alert Triggered',
      message: 'Page load time exceeded threshold on /analytics page.',
      type: 'warning',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2),
      read: false
    },
    {
      id: '3',
      title: 'Weekly Report Ready',
      message: 'Your weekly analytics report is ready for download.',
      type: 'info',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24),
      read: true
    }
  ]);

  const [isOpen, setIsOpen] = useState(false);

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notification => ({ ...notification, read: true }))
    );
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return {
    notifications,
    isOpen,
    setIsOpen,
    markAsRead,
    markAllAsRead,
    unreadCount
  };
}
