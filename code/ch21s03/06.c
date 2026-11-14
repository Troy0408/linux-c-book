...
#include <linux/config.h>
...
static int
isdn_ioctl(struct inode *inode, struct file *file, uint cmd, ulong arg)
{
...
#ifdef CONFIG_NETDEVICES
                        case IIOCNETGPN:
                                /* Get peer phone number of a connected
                                 * isdn network interface */
                                if (arg) {
                                        if (copy_from_user(&phone, argp, sizeof(phone)))
                                                return -EFAULT;
                                        return isdn_net_getpeer(&phone, argp);
                                } else
                                        return -EINVAL;
#endif
...
#ifdef CONFIG_NETDEVICES
                        case IIOCNETAIF:
...
#endif                          /* CONFIG_NETDEVICES */
...