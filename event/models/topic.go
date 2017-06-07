package models

type Topic interface {
	Subscribe() chan interface{}
	Unsubscribe(c chan interface{})
	Publish(v interface{})
}

type SimpleTopic struct {
	listeners map[chan interface{}]int
	subc      chan chan interface{} //传递通道的通道
	unsubc    chan chan interface{} //传递通道的通道
	pubc      chan interface{}      //传递结构体对象的通道
}

func (t *SimpleTopic) bg() { //process at background to manage routine
	for {
		select {
		case v := <-t.pubc: //如果数据写入通道里能读到数据
			for c, _ := range t.listeners {
				select {
				case c <- v:
				default:
					select {
					case <-c:
					default:
					}
					c <- v //把读到的数据写到所有监听着的通道中
				}
			}
		case c := <-t.subc: //从申请的通道读取到通道
			t.listeners[c] = 0
		case c := <-t.unsubc:
			delete(t.listeners, c) //删除通道
		}
	}
}

func New() Topic {
	topic := &SimpleTopic{listeners: make(map[chan interface{}]int),
		subc:   make(chan chan interface{}), //传递通道的通道
		unsubc: make(chan chan interface{}), //传递通道的通道
		pubc:   make(chan interface{}, 16)}
	go topic.bg()
	return topic
}

func (t *SimpleTopic) Subscribe() chan interface{} { //申请通道
	c := make(chan interface{}, 16)
	t.subc <- c
	return c
}

func (t *SimpleTopic) Unsubscribe(c chan interface{}) { //注销通道
	t.unsubc <- c
}

func (t *SimpleTopic) Publish(v interface{}) { //往通道中发布数据
	t.pubc <- v
}
